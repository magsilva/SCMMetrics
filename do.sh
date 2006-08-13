i=0
while [ $i != 350 ]
do
	mkdir $i
	cd $i
	svn checkout -r $i http://www.magsilva.dynalias.net/svn/wikire/trunk .
	sloccount --duplicates --autogen --addlangall . > ../stats-trunk.$i
	cd ..
	rm -rf $i

	mkdir $i
	cd $i
	svn checkout -r $i http://www.magsilva.dynalias.net/svn/wikire/branches .
	if [ -d nosafe ]; then
		cd nosafe
		sloccount --duplicates --autogen --addlangall . > ../../stats-nosafe.$i
		cd ..
	fi
	cd ..
	rm -rf $i

	let "i+=1"
done
