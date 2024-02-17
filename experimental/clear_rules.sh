#!/bin/bash

for ((i=1; i<=$1; i++))
do
  echo "del $i"
  sudo ovs-ofctl del-flows s"$i"
  sudo ovs-ofctl del-groups s"$i"
done