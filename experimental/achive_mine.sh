target=result/mine/achive/"$1"
mkdir $target
mkdir $target/libtins
mkdir $target/iperf
mv result/mine/iperf/* $target/iperf
mv result/mine/libtins/* $target/libtins
mv result/mine/ev_setting.json $target/
mv result/mine/routing_trees.json $target/