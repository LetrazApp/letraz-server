sudo docker build -t letraz-server:Django .
sudo docker run --env-file .env --name letraz-server -p 8000:8000 -d letraz-server:Djnago --workers=[NO_OF_WORKERS_INTENDED]