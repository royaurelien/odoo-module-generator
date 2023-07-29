# Build


**Requirements**

```bash

pip install -e .

```

## Build package for Pypi

```bash

pip install twine

```

Check setup.py

```bash

python3 setup.py check

```

Build distribution

```bash

python3 setup.py sdist

```

or

```bash

python3 -m build

```

Upload package to Pypi repo

```bash

twine upload --repository-url https://test.pypi.org/legacy/ dist/*

```

Test package

```bash

pip install -i https://test.pypi.org/simple/ myapp==0.0.1

```



Finnaly, upload to Pypi

```bash

twine upload dist/*

```

## Test with Docker

```bash

./test_python310.sh

```

or

```bash

docker run -v `pwd`:`pwd` -w `pwd` --name pytest -it -d python:3.10
docker exec -it pytest bash

```

```bash

$ pip install -e .
$ myapp [...]

```
```bash

./clear.sh

```

or

```bash

docker stop pytest && docker rm pytest

```
