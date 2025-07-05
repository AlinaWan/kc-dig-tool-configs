# AZERTY keyboard users

The macro does **not support importing walk patterns that use AZERTY-style movement keys** (`ZQSD`). Only patterns using `W`, `A`, `S`, and `D` are supported for import.

If you try to import a `.json` file and see an error like:

> `Invalid moves (only W, A, S, D allowed)`

…it means the file was created using **AZERTY keys**, which the macro cannot recognize.

## What you can do:

If you're using an AZERTY keyboard, consider using a **community fork that adds AZERTY support**:

* **Download precompiled binaries** (no setup required):
  [`https://github.com/AlinaWan/dig-tool-azerty-bin/releases`](https://github.com/AlinaWan/dig-tool-azerty-bin/releases)

  > This is **just a binary mirror** of the fork below — useful if you don’t want to build it yourself.

* **Or build from the actual source fork**:
  [`https://github.com/sltcvtfk/dig-tool`](https://github.com/sltcvtfk/dig-tool)

  > This is a fork of the original project that adds AZERTY support.

> These versions are **community-maintained forks** and are **not official releases**. Use them at your own discretion.
