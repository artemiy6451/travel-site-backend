from faststream.rabbit import RabbitBroker


def _get_rabit_broker() -> RabbitBroker:
    return RabbitBroker()


rabbit_broker = _get_rabit_broker()
