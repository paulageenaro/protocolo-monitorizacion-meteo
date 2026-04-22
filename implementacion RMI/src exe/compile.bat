@echo off
mkdir bin 2>nul
mkdir lib 2>nul

REM Descarga json-simple si no existe (requiere curl, incluido en Win10+)
IF NOT EXIST lib\json-simple-1.1.1.jar (
    echo Descargando json-simple...
    curl -L -o lib\json-simple-1.1.1.jar ^
        https://repo1.maven.org/maven2/com/googlecode/json-simple/json-simple/1.1.1/json-simple-1.1.1.jar
)

javac -cp lib\json-simple-1.1.1.jar -d bin src\meteo\*.java
echo Compilacion completada.
