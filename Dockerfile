FROM --platform=amd64 localstack/localstack:latest-amd64 as lstack64

RUN curl -L https://raw.githubusercontent.com/warrensbox/terraform-switcher/release/install.sh | bash
RUN tfswitch 1.3.3
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - &&\
    apt-get install -y nodejs
RUN npm i -g serverless
# RUN awslocal secretsmanager create-secret \
#     --name DBParams \
#     --description "My test secret created with the CLI." \
#     --secret-string "{\"user\":\"hippy\",\"password\":\"pippy\",\"host\":\"http://localhost:5432\",\"db\":\"yippy\"}"
COPY ./infra/lambda-gateway.tf /home/localstack/app/infra/
COPY ./src/get_key.py /home/localstack/app/src/
COPY ./infra/start_env.sh /home/localstack/app/infra/
COPY ./api-gtw-acck /home/localstack/app/serverless
RUN echo "Start the shell file on /home/localstack/app"