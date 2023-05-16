FROM localstack/localstack:2.0.2

RUN curl -L https://raw.githubusercontent.com/warrensbox/terraform-switcher/release/install.sh | bash
RUN tfswitch 1.3.3
RUN terraform init
COPY ./infra/lambda-gateway.tf /home/localstack/app/infra/
COPY ./src/lambda.py /home/localstack/app/src/
COPY ./infra/start_env.sh /home/localstack/app/infra/
RUN echo "Start the shell file on /home/localstack/app"