
import os,sys,shutil
from domino.core import log, start_log
from domino.server import Server
from domino.jobs import Job
from domino.globalstore import GlobalStore
from update import install, activate

if __name__ == "__main__":
    try:
        job_id = sys.argv[1]
        with Job.open(job_id) as job:
            job.log(f'{job.params.get("argv")}')
            product = job.arg(0)
            job.start_if_not_exists(f'install.{product}', f'Установка последней версии "{product}"')
            config = Server.get_config()
            version = install(job, product)
            active_version = Server.get_active_version(product)
            if active_version is not None and active_version.is_draft:
                job.log(f'Версия {product}.{version} не будет активирована, поскольку ативна версия в разработке {active_version}')
            else:
                activate(job, product, version)
    except:
        start_log.exception('domino.install')
