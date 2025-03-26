 #!/bin/bash

 source venv/bin/activate
 gunicorn -w4 -b localhost:8000 "api:create_app()"
