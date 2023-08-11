# aico2caom2
A Docker image containing the tools to update and archive files, and to generate CAOM2 Observations from Allen I Carswell Observatory (AICO).

# Table of contents
1. [Set Up (One Time Only)](#set_up)
    1. [Build the Image](#build)
    1. [Credentials](#creds)
    1. [File Location](#working_dir)
1. [Initialize Workspace (One Time Only)](#initialize)
1. [Prepare Sky Camera Images](#prepare_sky)
1. [Ingest Sky Camera Images](#aico_run)
1. [Debugging](#debugging)


# How To Use aico2caom2

These are Linux-centric instructions.

# Set Up (one time only) <a name="set_up"></a>

## Docker Image <a name="build"></a>

In an empty directory (the 'working directory'), on a machine with Docker installed:

1. In the main branch of this repository, find the file `Dockerfile` and copy it to the working directory.

1. To build the container image, run this:

   ```
   docker build -f Dockerfile -t aico2caom2_app ./
   ```

## Credentials <a name="creds"></a>

1. Run the following command to create a proxy certificate file in the working directory. You will be prompted for the password, unless you have an appropriately configured `.netrc` file:

   ```
   docker run --rm -ti --user $(id -u):$(id -g) -e HOME=/usr/src/app -v ${PWD}:/usr/src/app aico2caom2_app cadc-get-cert --cert-filename /usr/src/app/cadcproxy.pem --days-valid 10 -u <CADC User Name here>
   ```

1. The `aico_run*.sh` scripts described later will attempt to copy `$HOME/.ssl/cadcproxy.pem` to the 'working directory', so copy `cadcproxy.pem` to `$HOME/.ssl/`. 

1. The proxy certificate file will be valid for 10 days, and must be periodically renewed. At the moment, it is possible to use a [.netrc](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html) file and a cron job to automatically renew the certificate. Add something like the following to a crontab:

   ```
   0 0 * * *  docker run --rm -ti --user $(id -u):$(id -g) -e HOME=/usr/src/app -v ${PWD}:/usr/src/app aico2caom2_app cadc-get-cert -n -q --cert-filename /usr/src/app/cadcproxy.pem --days-valid=25 
   ```

   Modify the `aico_run*.sh` scripts to use the location of the renewed certificate file `cadcproxy.pem`.


## File Location <a name="working_dir"></a>

`aico2caom2` can store files from local disk to CADC storage. This behaviour is controlled by configuration
information, located in a file named `config.yml`. Most of the `config.yml` values are already set appropriately, but there are a few values that need to be
set according to the execution environment. For a complete description of the `config.yml` content, see
https://github.com/opencadc/collection2caom2/wiki/config.yml.

1. Copy the file `config.yml` to the working directory. e.g.:

   ```
   wget https://raw.github.com/opencadc/aico2caom2/main/config/config.yml
   ```

1. Tell `aico2caom2` in `config.yml` what to do with files on disk after the files have been stored to CADC:

   1. Set `cleanup_files_when_storing` to `True` or `False`. 
       1. If this is set to `False`, `aico2caom2` will do nothing with the files on disk.
       1. If this is set to `True`, `aico2caom2` will move stored files to either a success or failure location.

   2. If `cleanup_files_when_storing` is set to `True`, set `cleanup_failure_destination`  and `cleanup_success_destination` to fully-qualified directory names that are visible within the Docker container. A directory is visible within a Docker container if it
      is one of the values on the right-hand-side of the colon in a `-v` `docker run` parameter.

1. Tell `aico2caom` in `config.yml` whether to re-submit duplicate files.
   1. Set `store_modified_files_only` to `True` or `False`. If this is set to `False`, there is no effect on execution. If this is set to true, `aico2caom2`
      checks that the local version of the file has a md5 checksum that is different from the file at CADC before transferring the file to CADC storage. This affects only the `store` `task_types`.


# Initialize Execution Location (one time only) <a name="initialize"></a>

1. In the main branch of this repository, find the scripts directory, and copy the files `aico_run.sh`  and `aico_run_incremental.sh` to the working directory. e.g.:

   ```
   wget https://raw.github.com/opencadc/aico2caom2/aico/scripts/aico_run.sh
   wget https://raw.github.com/opencadc/aico2caom2/aico/scripts/aico_run_incremental.sh
   ```

1. Ensure the scripts are executable:

   ```
   chmod +x aico_run.sh
   chmod +x aico_run_incremental.sh
   ```

1. Edit the scripts to specify the file location:

   1. `aico_run.sh`:
      1. Find this line: `docker run --rm --name ${COLLECTION}_todo  --user $(id -u):$(id -g) -e HOME=/usr/src/app -v ${PWD}:/usr/src/app/ -v /data:/data ${IMAGE} ${COLLECTION}_run || exit $?`
      2. Replace the `/data/:` portion of the command with the fully-qualified directory name of where the application should find the data. This directory will be called the "data source directory" in these instructions. 

   1. `aico_run_incremental.sh`:
      1. Find this line: `docker run --rm --name ${COLLECTION}_state  --user $(id -u):$(id -g) -e HOME=/usr/src/app -v ${PWD}:/usr/src/app/ -v /data:/data ${IMAGE} ${COLLECTION}_run_incremental || exit $?`
      2. Replace the `/data/:` portion of the command with the fully-qualified directory name of where the application should find the data.

# How To Prepare AICO Sky Camera Images for CADC Ingestion <a name="prepare_sky"></a>

FITS files archived at CADC are checked with `fitsverify` before being stored. This step will update FITS file headers in a file so that the keyword value pairs conform to the `fitsverify` check.

1. The data source directory needs to be on a machine with access to Sky Camera Images, and enough disk space to make a copy of the files to be archived. 

1. On a machine with write access to the data source directory, run this:

   ```
   docker run --rm -ti --user $(id -u):$(id -g) -e HOME=/usr/src/app -v ${PWD}:/usr/src/app -v <data source directory>:/data aico2caom2_app /bin/bash -c 'for ii in $(ls /data/*fits); do python /usr/local/bin/aico_weathercam.py ${ii}; done'
   ```

This will run the script `aico_weathercam.py` for each `<file_name.fits>` in `/data`.

All `<file name.fits>` in the data source directory will be copied to `<file name_v.fits>`. The `<file name_v.fits>` files should be archived at CADC.

Prepared files should be stored in a separate location for the next step, as `aico2caom2` will try to process any files with a `.fits` extension.

# How to Store Files and Create CAOM2 Records at CADC <a name="aico_run"></a>

`aicocaom2` may be run so that it processes files incrementally, according to their timestamp on disk, or so that is processes all the files it finds.

1. To run the application incrementally:

   ```
   ./aico_run_incremental.sh
   ```
   By default, incremental mode will start 24 hours prior to the current execution time. This can be changed by modifying the `state.yml` file content that is created on the first run.

1. To run the application on all the files it finds:

    ```
    ./aico_run.sh
    ```

# Debugging <a name="debugging"></a>

1. To debug the application from inside the container, run the following command. Replace the `<data directory here>` with the fully-qualified path name of the directory where the data to be processed is located.

   ```
   user@dockerhost:<cwd># docker run --rm -ti -v ${PWD}:/usr/src/app -v <data directory here>:/data --user $(id -u):$(id -g) -e HOME=/usr/src/app --name aico_run aico2caom2_app /bin/bash
   cadcops@53bef30d8af3:/usr/src/app# aico_run
   ```

1. For some instructions that might be helpful on using containers, see:
   https://github.com/opencadc/collection2caom2/wiki/Docker-and-Collections

1. For some insight into what's happening, see: https://github.com/opencadc/collection2caom2

1. For Docker information, see: https://www.docker.com
