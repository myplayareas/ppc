# ppc

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

6.2 Register a new user (OK)

6.3 Create new repository (OK)

6.4 View created repository (OK)

6.5 Analyse the repository (OK)

6.6 View details about analysed repository (OK)

![Tela Principal](https://github.com/myplayareas/ppc/blob/main/docs/TelaPrincipal.png)

[![asciicast](https://asciinema.org/a/428602.svg)](https://asciinema.org/a/428602)
