target=result/stp/achive/"$1"
mkdir $target
mkdir $target/libtins
mkdir $target/iperf
mv result/stp/iperf/* $target/iperf
mv result/stp/libtins/* $target/libtins
mv result/stp/ev_setting.json $target/
mv result/stp/routing_trees.json $target/