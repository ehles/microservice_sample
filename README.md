# SSE (Server Sent Events) example

This is a simple example of using SSE (Server Sent Events) in Flask.

## Demo

<img src="./img/demo.webp" width="600">

## Usage

### Install dependencies
1. Install dependencies
```bash
pip install -r requirements.txt
```

### Run the web server

1. Run the server
```bash
python web.py
```

2. Open http://localhost:5000 in your browser

### Run a micro services

1. Each micro service is a separate terminal window
```bash
python ./app.py -l 5010 -n T -t 1000
python ./app.py -l 5011 -n DS -t 800
python ./app.py -l 5012 -n TM -t 1500
python ./app.py -l 5013 -n V -t 4000 -s 127.0.0.1:5010 -s 127.0.0.1:5011 -s 127.0.0.1:5012
python ./app.py -l 5014 -n P -t 4000 -s 127.0.0.1:5013 -s 127.0.0.1:5017
python ./app.py -l 5017 -n H -t 1000
python ./app.py -l 5015 -n D -t 4000 -s 127.0.0.1:5014
python ./app.py -l 5016 -n UI -t 4000 -s 127.0.0.1:5015
```

### Send requests to the micro services

1. In a separate terminal window run
```bash
curl -X POST http://localhost:5016/activate -H "Content-Type: application/json" -d '{"item": "V", "color": "red"}'
```
