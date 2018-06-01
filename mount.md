docker run --rm --name shbaam -v /c/Users/tdhttt/workspace/shbaam/iobackup/input:/home/shbaam/input -v /c/Users/tdhttt/workspace/shbaam/iobackup/output/:/home/shbaam/output -it chdavid/shbaam

docker run --rm --name shbaam -v "$(pwd)/input":/home/shbaam/input -v "$(pwd)/output":/home/shbaam/output -it chdavid/shbaam
