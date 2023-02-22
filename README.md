# Kit-exts-ndi

Experimenting with ndi feed in Omniverse. See [video](./2023-02-17%2016-23-32.mp4) for demo.

## Getting started

- Requires Kit >= 104.1
- Tested in Create 2022.3.1
- Not working in Code 2022.3.1

```
$ ./link_app.bat --app create
$ ./app/omni.create.bat --/rtx/ecoMode/enabled=false --ext-folder exts --enable fredericl.ndi.experimentation
```

From the extension window, select the ndi source (the R button refreshes the list, the L button makes a more thorough search, but will freeze the app for no more than a few seconds). The parent prim option allow you to decide where we'll spawn the necessary scene elements, leave blank for default prim. You can start the stream and create the scene elements (via their respective buttons) independently of each other, or in any order.

Using the ndi tests patterns, I've noticed that the Omniverse texture is not always quick to respond to changes. I've found that wiggling the viewport force it to update.

Performance: I usually get about 15-20 fps for a ndi stream output format of 1080p30. Note that the plane's size as well as the internal ndi fetch fps are hardcoded to match that of the output format.

## Resources
- [kit-cv-video-example](https://github.com/jshrake-nvidia/kit-cv-video-example)
- [kit-dynamic-texture-example](https://github.com/jshrake-nvidia/kit-dynamic-texture-example)
- [ndi-python](https://github.com/buresu/ndi-python)
