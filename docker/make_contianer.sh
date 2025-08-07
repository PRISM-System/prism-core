docker run -it \
        --gpus all \
        -h jaeheekim \
        -p 1248:8920 \
        --ipc=host \
        --name jaehee-agi \
        -v /home/jaeheekim/codes/prism:/workspace/codes \
        -v /data4:/workspace/CACHE \
        jaehee/alienlm:250102 \
    bash
