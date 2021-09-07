# Generic Extract Generator 
This program can be used to extract the data from database and send it over email.

## Usage

```bash
generic_extract_generator.py <Configuration File E.g. customer_extract.cfg>
```
Configuration files are stored in /config folder.

SQL files are stored in /sql folder.

All the logs are stored in generic_extract_generator.log file.

## Caveats

The script is using unrestricted Sqlite database. 
The connection will need to be tweaked as per the underlying database/datasource with necessary python modules.

