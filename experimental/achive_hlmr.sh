target=result/hlmr/achive/"$1"
mkdir $target
mkdir $target/libtins
mkdir $target/iperf
mv result/hlmr/iperf/* $target/iperf
mv result/hlmr/libtins/* $target/libtins
mv result/hlmr/ev_setting.json $target/
mv result/hlmr/routing_trees.json $target/