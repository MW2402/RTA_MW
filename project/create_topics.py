from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from config import (
    BROKER,
    TOPIC_INVENTORY,
    TOPIC_SCORED,
    TOPIC_ALERTS,
    TOPIC_ONLINE_TRAINING,
)

TOPICS = [
    TOPIC_INVENTORY,
    TOPIC_SCORED,
    TOPIC_ALERTS,
    TOPIC_ONLINE_TRAINING,
]


def create_admin_client() -> KafkaAdminClient:
    return KafkaAdminClient(
        bootstrap_servers=BROKER,
        client_id="stockout-topic-manager",
    )


def create_topics() -> None:
    admin_client = create_admin_client()

    try:
        existing_topics = admin_client.list_topics()

        topics_to_create = []

        for topic_name in TOPICS:
            if topic_name not in existing_topics:
                topics_to_create.append(
                    NewTopic(
                        name=topic_name,
                        num_partitions=1,
                        replication_factor=1,
                    )
                )

        if not topics_to_create:
            print("All required Kafka topics already exist.")
            return

        admin_client.create_topics(
            new_topics=topics_to_create,
            validate_only=False,
        )

        print("Created topics:")
        for topic in topics_to_create:
            print(f"  - {topic.name}")

    except TopicAlreadyExistsError:
        print("One or more topics already exist.")

    finally:
        admin_client.close()


def main() -> None:
    create_topics()


if __name__ == "__main__":
    main()