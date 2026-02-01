import argparse
from google.cloud import storage


def main():
    parser = argparse.ArgumentParser(
        description="Create (if not exists) the Google Cloud Storage bucket to act as backend and store the IaC state."
    )

    parser.add_argument(
        "bucket_name",
        type=str,
        nargs="?",  # Makes the positional argument optional
        default="bkt-infra-state",
        help="Name for the bucket. Remember that the name needs to be globally unique. (default: '<project>-bkt-infra-state')",
    )

    parser.add_argument(
        "--location",
        type=str,
        default="us-east1",
        help="Location of where to deploy the bucket. (default: 'us-east1')",
    )

    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="GCP Project ID to create the bucket in. If not provided, uses the currently active project in gcloud config.",
    )

    parser.add_argument(
        "--users",
        type=str,
        nargs="*",  # allow no users
        help="Google Cloud users to grant access to the bucket to manage infra.",
    )

    parser.add_argument(
        "--clean", action="store_true", help="Delete bucket and user permissions"
    )
    args = parser.parse_args()

    # Pass the project explicitly if provided; otherwise, let the client infer it from environment
    st_client = storage.Client(project=args.project)

    bkt = storage.Bucket(st_client, f"{st_client.project}-{args.bucket_name}")

    if not bkt.exists():
        bkt.storage_class = "STANDARD"

        # When creating, we must use the client.create_bucket method to actually send the API request
        # st_client.create_bucket(bucket_or_name, location=...)
        bkt = st_client.create_bucket(bkt, location=args.location)

        bkt.iam_configuration.uniform_bucket_level_access_enabled = True
        bkt.patch()

        print(f"Created bucket {bkt.name} in project {st_client.project} with:")
        print(f" - Location: {bkt.location}")
        print(f" - Storage Class: {bkt.storage_class}")
        print(" - Uniform Bucket-Level Access: Enabled")

    else:
        print(f"Bucket {bkt.name} already exists in project {st_client.project}.")

    if args.users:
        print("Manage user access to bucket")

        target_role = "roles/storage.objectUser"
        policy = bkt.get_iam_policy(requested_policy_version=3)

        # Find existing binding for the role
        role_binding = next(
            (b for b in policy.bindings if b["role"] == target_role),
            None,
        )

        for user in args.users:
            gcp_user = "user:" + user

            if role_binding:
                if gcp_user in role_binding["members"]:
                    print(f" - {user} already has access to {bkt.name}")
                    continue
                else:
                    role_binding["members"].add(gcp_user)
            else:
                # If the role binding doesn't exist yet, create it
                new_binding = {"role": target_role, "members": {gcp_user}}
                policy.bindings.append(new_binding)
                # Refresh reference to the new binding for subsequent users in this loop
                role_binding = new_binding

        bkt.set_iam_policy(policy)
        print(f" - Updated access policies for {bkt.name}")


if __name__ == "__main__":
    main()
