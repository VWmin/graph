target=result/igmp/achive/"$1"
mkdir $target
mkdir $target/libtins
mkdir $target/iperf
mv result/igmp/iperf/* $target/iperf
mv result/igmp/libtins/* $target/libtins
mv result/igmp/ev_setting.json $target/
mv result/igmp/cost $target/