# FLEX-DSO
> Destribution Service Operator (DSO) client to test the FLEX market platform via its REST interface.
The DSO client sends flexibility demand to the flex market platform, either random or per input time series.


## Installation

```sh
cd preferred-folder
git clone UniK-INES/FLEX-DSO
```

## Usage example

Run FLEX-DSO using docker (see wiki for more env. var. options):

OS X & Linux:

```sh
cd preferred-folder
export FLEX_SERVER=flexmarket:8080
docker build -t flex-dso .
docker run -it -e FLEX_SERVER=127.0.0.1:8080 --network="host" flex-dso
```

Windows:

```sh
cd preferred-folder
SET FLEX_SERVER=flexmarket:8080
docker build -t flex-dso .
docker run -it -e FLEX_SERVER=host.docker.internal:8080 flex-dso
```

Usually, the FLEX-DSO client is startet with other docker services using docker-compose. See FLEX for instructions.

## Development setup

Requirements:

* python
* pip

```sh
cd preferred-folder
pip install -r ./requirements.txt

```

## How to contribute

Pull requests welcome!

1. Fork it (<https://github.com/UniK-INES/FLEX-DSO/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

## Release History

* 0.0.1
    * Work in progress

## Meta

Dr. Sascha Holzhauer – [Website](https://uni-kassel.de/go/holzhauer) – Sascha.Holzhauer@uni-kassel.de

Distributed under the GPLv3 license. See ``LICENSE`` for more information.

<!-- Markdown link & img dfn's -->
[wiki]: https://github.com/UniK-INES/FLEX-DSO/wiki
