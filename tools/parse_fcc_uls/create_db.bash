if [ ! -f l_amat.zip ]; then
    echo "Downloading Amature Radio License Data"
    curl -o l_amat.zip https://data.fcc.gov/download/pub/uls/complete/l_amat.zip
fi


if [ ! -f l_gmrs.zip ]; then
    echo "Downloading GMRS License Data"
    curl -o l_gmrs.zip https://data.fcc.gov/download/pub/uls/complete/l_gmrs.zip
fi


if [ ! -f fcc_uls.db ]; then
    echo "Creating sqlite database 'fcc_uls.db'"
    python create_db.py
    echo "Database 'fcc_uls.db' created. Copy this to the APRS Assistant ./data directory to enable license lookups." 
else
    read -p "fcc_uls.db already exists. Overwrite? " yn
    if [[ "$yn" =~ "y" ]]; then
    	echo "Backing up 'fcc_uls.db' to 'fcc_uls.bak'"
        mv fcc_uls.db fcc_uls.db.bak
    	echo "Overwriting sqlite database 'fcc_uls.db'"
    	python create_db.py
    	echo "Database 'fcc_uls.db' created. Copy this to the APRS Assistant ./data directory to enable license lookups." 
    fi
fi
