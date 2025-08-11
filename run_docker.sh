# docker container prune -f;docker image prune -f
docker build -t zpv10 --progress=plain .
docker run \
-p 8001:80 \
 --mount type=bind,src="$(pwd)/.env.prod",dst=/app/.env.prod \
 --mount type=bind,src=/mnt/zooscan_pool/zooscan/remote/complex/piqv/plankton/zooscan_lov,dst=/zooscan_lov \
 zpv10


