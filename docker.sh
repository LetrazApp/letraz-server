sudo docker build -t letraz-server:Djnago .
sudo docker run --env-file .env --name letraz-server -p 8000:8000 -d letraz-server:Djnago