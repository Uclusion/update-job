#!/usr/bin/env -S python3 -B

# NOTE: If you are using an alpine docker image
# such as pyaction-lite, the -S option above won't
# work. The above line works fine on other linux distributions
# such as debian, etc, so the above line will work fine
# if you use pyaction:4.0.0 or higher as your base docker image.

import sys
import logging
import re

if __name__ == "__main__" :
    secret_key_id = sys.argv[1]
    secret_key = sys.argv[2]
    commit_message = sys.argv[3]

    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s: %(message)s')
    logger.info('GitHub Event message: %s', commit_message)
    logger.info('secret key id: %s', secret_key_id)

    regex = r'([A-Z]+-[A-Za-z]+-\d+)'
    extracted = None

    # extract from 'https://stage.uclusion.com/dd56682c-9920-417b-be46-7a30d41bc905/J-Marketing-9'
    # or 'J-Marketing-9 some text'
    match_url = re.search(regex, commit_message)
    if match_url:
        extracted = match_url.group(1)

    # Extract from text
    match_text = re.search(regex, commit_message)
    if match_text:
        extracted = match_text.group(1)

    if extracted is not None:
        logger.info('extracted %s', extracted)


    # This is how you produce workflow outputs.
    # Make sure corresponds to output variable names in action.yml
    # if "GITHUB_OUTPUT" in os.environ :
    #     with open(os.environ["GITHUB_OUTPUT"], "a") as f :
    #         print("{0}={1}".format("output-one", output1), file=f)
    #         print("{0}={1}".format("output-two", output2), file=f)