#!/usr/bin/env -S python3 -B

# NOTE: If you are using an alpine docker image
# such as pyaction-lite, the -S option above won't
# work. The above line works fine on other linux distributions
# such as debian, etc, so the above line will work fine
# if you use pyaction:4.0.0 or higher as your base docker image.

import sys
import logging

if __name__ == "__main__" :
    githubToken = sys.argv[1]
    githubEvent = sys.argv[2]
    secretKeyId = sys.argv[3]
    secretKey = sys.argv[4]

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('GitHub Event:')
    logger.info(githubEvent)

    logger.info('secret key id:', secretKeyId)


    # This is how you produce workflow outputs.
    # Make sure corresponds to output variable names in action.yml
    # if "GITHUB_OUTPUT" in os.environ :
    #     with open(os.environ["GITHUB_OUTPUT"], "a") as f :
    #         print("{0}={1}".format("output-one", output1), file=f)
    #         print("{0}={1}".format("output-two", output2), file=f)