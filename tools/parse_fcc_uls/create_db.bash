if [ ! -f l_amat.zip ]; then
    wget https://data.fcc.gov/download/pub/uls/complete/l_amat.zip
fi


if [ ! -f l_gmrs.zip ]; then
    wget https://data.fcc.gov/download/pub/uls/complete/l_gmrs.zip
fi


if [ ! -f fcc_uls.db ]; then
    python create_db.py
else
    read -p "fcc_uls.db already exists. Overwrite? " yn
    if [[ "$yn" =~ "y" ]]; then
	echo "HERE!"
        mv fcc_uls.db fcc_uls.db.old
    	python create_db.py
    fi
fi
