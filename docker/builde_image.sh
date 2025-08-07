image_name=jaehee/alienlm_axolotl:250718
docker build -t $image_name --build-arg UNAME1=jaeheekim \
                            --build-arg UID1=$(id --user jaeheekim) \
                            --build-arg GID=$(id -g) \
                            .