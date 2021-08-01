# ppc

Cria uma aplicação em Python para simular um produtor e um consumidor usando Threads

Fluxo do diretório app (script python my_app_repositories_2.py): 

1. Dado um conjunto de clientes

2. Cada cliente envia um repositório git para ser analisado

3. Cada requisição é inserida em uma fila de repositórios

4. Existe um consumidor que vai analisar a fila de repositórios

5. Para cada repositório da fila é criada uma nova thread para analisar o repositório de acordo com a ordem de chegada

[![asciicast](https://asciinema.org/a/eiY4BQwwL1lOwQLrlhctWAfYa.png)](https://asciinema.org/a/eiY4BQwwL1lOwQLrlhctWAfYa)

Fluxo da aplicação web myapp: 

The myapp is a web application that prototypes some basic analysis of repositories. It uses the pydriller (https://github.com/ishepard/pydriller) to analyze and mining data from software repositories. 

It was created using the flask framework (https://flask.palletsprojects.com).

1. Clone the repository

2. Install dependencies
```
pip install pydriller

```
3. Set environment variables
```
. setvariables.sh
```

4. Restart database (optional)
```
flask init-db
```

5. Run application
```
flask run
```

6. Functional regression tests that must be performed:

6.1 Login (OK)

6.2 Register a new user

6.3 List of repositories of the logged in user (OK)

6.4 Create new repository

6.5 View created repository

6.6 Analyse the repository

[![asciicast](https://asciinema.org/a/428273.svg)](https://asciinema.org/a/428273)
