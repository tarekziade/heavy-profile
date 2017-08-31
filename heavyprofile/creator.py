import os
import sys
import argparse
import asyncio

from arsenic import get_session
from arsenic.browsers import Firefox
from arsenic.services import Geckodriver, free_port, subprocess_based_service

from heavyprofile.util import fresh_profile
from heavyprofile import logger


class CustomGeckodriver(Geckodriver):
    async def start(self):
        port = free_port()
        await self._check_version()
        return await subprocess_based_service(
            [self.binary, '--port', str(port), '--marionette-port', '50499'],
            f'http://localhost:{port}',
            self.log_file
        )


WORDS = os.path.join(os.path.dirname(__file__), 'words.txt')
with open(WORDS) as f:
    WORDS = f.readlines()


URLS = os.path.join(os.path.dirname(__file__), 'urls.txt')
with open(URLS) as f:
    URLS = f.readlines()


def next_url():
    for url in URLS:
        url = url.strip()
        if url.startswith('#'):
            continue
        for word in WORDS:
            word = word.strip()
            if word.startswith('#'):
                continue
            yield url % word


firefox = '/Applications/FirefoxNightly.app/Contents/MacOS/firefox'


async def build_profile(profile_dir, max_urls=2):
    logger.msg("Updating profile located at %r" % profile_dir)
    caps = {"moz:firefoxOptions": {"binary": firefox,
                                   "args": ["-profile", profile_dir],
                                   }}
    logger.msg("Starting the Fox...")
    with open('gecko.log', 'a+') as glog:
        async with get_session(CustomGeckodriver(log_file=glog),
                               Firefox(**caps)) as session:
            for current, url in enumerate(next_url()):
                logger.visit_url(index=current+1, url=url)
                await session.get(url)
                if current == max_urls:
                    break

    logger.msg("Done.")


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Profile Creator')
    parser.add_argument('profile', help='Profile Dir', type=str)
    args = parser.parse_args(args=args)
    if not os.path.exists(args.profile):
        fresh_profile(args.profile)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(build_profile(args.profile))
    finally:
        loop.close()


if __name__ == '__main__':
    main()
