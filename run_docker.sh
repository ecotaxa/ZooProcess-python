
docker run \
-p 8001:80 \
 --mount type=bind,src="$(pwd)/.env.prod",dst=/app/.env.prod \
 --mount type=bind,src=/mnt/zooscan_pool/zooscan/remote/complex/piqv/plankton/zooscan_lov,dst=/zooscan_lov \
 ecotaxa/zooprocess_v10:latest


