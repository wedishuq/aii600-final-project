# Data

The notebook reads local files from this folder. The event exports and the product status list come from internal systems. They are not republished, and they are not in git. `data/*` is ignored except this file.

There is no public download. The event files are an endpoint-security export of file-detection events, with columns `_time` and `_raw` (the event JSON). The product status list is the export downloaded on 2026-11-16.

- `Days_61_90.csv`, `Days_31_60.csv`, `Days_01_30.csv`. Device time runs from 2026-08-16 22:54 local time through 2026-11-16 12:45 local time. The names are not three disjoint months: the two later files overlap, and each file stops at a round row count (31,000, 31,000, 29,000).
- `DevToolStatus.csv`. Product status list, 10,000 rows, columns `publisher`, `prod_name`, `u_version`, `u_tag`, `u_dev_tool_status`, `u_link`, `u_download`, `u_install_count`. The status and the install count are as of 2026-11-16.

SHA-256:

- `9403d78cb321eed6ebeffc61afc0b2d23b1ba5a4862fc35f51d3ac9afc2a9ed8` `Days_01_30.csv`
- `2fc71d8ae7ddd62bcfcc79bc8185de8abdab0046a37ad8344fb6c18984364e6e` `Days_31_60.csv`
- `1afa084a6d03297b553e8befe8fa876c7dee29194293622b0cf0c3930a480aab` `Days_61_90.csv`
- `084887a9cbbe97b92d0032de0a0e4a9fd1d60a1a922e92bae8fecd053c654ba2` `DevToolStatus.csv`

The unit of observation in the notebook is one event `uuid`. Pooling the three files and keeping the earliest copy of each `uuid` gives 27,496 events. The scored rows are the ones whose opening process, `actor.app_name`, matches a product name on the list.
