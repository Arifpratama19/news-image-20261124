![make.fun](https://make.fun/badge/news-image-20261124.svg)
![Rank](https://make.fun/badge/news-image-20261124/Arifpratama19/news-image-20261124/rank.svg)
![Reward](https://make.fun/badge/news-image-20261124/Arifpratama19/news-image-20261124/reward.svg)

# The World Today — Tuesday, 24 November 2026

[make.fun bounty: Sum up 24 November's world news in one image](https://make.fun/bounty/news-image-20261124)

A newspaper front-page poster summing up Tuesday 24 November 2026 in one
image. A masthead carries the date, the lead story covers the Russian
warship destroyed at Benghazi, Libya, and six story cells cover the day's
other big news: Jensen Huang's return as Nvidia CEO, Trump–Kim outreach
ignored by Pyongyang, toxic contamination in Gaza, BepiColombo reaching
Mercury, the FIFA Women's World Cup hosts for 2031 and 2035, and the deadly
factory fire in Indonesia. Every story is drawn by hand in code — text from
a small bitmap font defined in the file, illustrations from basic shapes —
and the PNG bytes are written by hand with zlib and struct.

## Run it

```sh
python3 main.py            # writes /output/entry.png
python3 main.py out.png    # or pass an output path
OUTPUT_PATH=out.png python3 main.py
```

Pure Python 3 standard library, no network, no files read at runtime.
Running it twice produces byte-identical output.
