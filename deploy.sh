echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
echo "% NYU Shanghai LibSense Back-end Service Auto-Deployment %"
echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

echo "Please specify the location of desired configurations (default: /home/libsense):"
read ROOT_DIR

if [ ! $ROOT_DIR ]
then ROOT_DIR='/home/libsense'
fi

if [ ! -d $ROOT_DIR ]
then 
    mkdir $ROOT_DIR
    cd $ROOT_DIR

    echo "Project folder does not exist, creating a new one..."
    echo "Cloning project repository..."    
    git clone https://github.com/NYUSHLibraryAccess/LibSense-server.git
    cd "$ROOT_DIR/LibSense-server"
    git checkout main
    mkdir assets
    mkdir assets/to_del
    mkdir assets/source
    mkdir logs
    mkdir configs

    pip3 install -r requirements.txt
else
    echo "Pulling latest changes from repository..."
    cd "$ROOT_DIR/LibSense-server"
    git reset --hard HEAD
    git checkout main
    git pull

    pip3 install -r requirements.txt
fi

echo "Done!"