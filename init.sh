#!/bin/bash

if [[ $1 =  'dev' || $1 = 'pro' || $1 = 'test' ]]
then
cd gunicorn/ && \
touch gunicorn.conf && \
cat $1.conf > gunicorn.conf && \
cd ../  && \
cd instance/ && \
touch settings.cfg  && \
cat $1.cfg > settings.cfg
echo "初始化完成"
else
   echo "参数有误，只能是 dev || pro || test"
fi
