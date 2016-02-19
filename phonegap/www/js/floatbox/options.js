fb.options = {
//
// EDIT ONLY WITHIN THE FOUR OPTION BLOCKS BELOW.
// See the instructions for information about setting floatbox options.
// See the options reference for details about all the available options.
// Commas are required after each entry except the last entry in a block.
// A comma on the last entry in a block will cause the option settings to fail in some browsers.

// globalOptions is where you enter a license key and change default floatbox options site-wide.
// Use the configurator.html form in this folder to generate globalOptions preferences through form selections.

// When all your global option preferences are set to your liking,
// you can optimize the loading of Floatbox by removing any classOptions you don't use,
// minifying this file with a tool such as http://skalman.github.io/UglifyJS-online/
// and appending the resultant small code to the bottom of the floatbox.js file.

// globalOptions: {
//   // Paste your license key between the quotes below, or enter it in the configurator form.
//   // (Separate multiple license keys with spaces or commas.)
//   licenseKey: ""
// },

globalOptions: {
	licenseKey: "",
	showIE6EndOfLife: false,
	shadowSize: 2,
	shadowType: "halo",
	boxCornerRadius: 4,
	autoEndVideo: false,
	showPlayPause: false,
	pipIndexThumbs: false,
	showIndexThumbs: false,
	showItemNumber: false,
	enableKeyboardNav: false,
	showNewWindowIcon: false,
	showOuterClose: true,
	showClose: false,
	enableDragMove: false,
	stickyDragResize: false,
	autoFitMedia: false,
	autoFitImages: false,
	resizeDuration: 0,
	overlayFadeDuration: 0,
	crossFadeImages: false,
	doAnimations: false,
	overlayOpacity: 42,
	panelPadding: 8,
	padding: 4,
	colorTheme: "white",
	overlayFadeTime: 0.01,
	fadeTime: 0,
	measureHTML: true,
	outerBorder: 0,
	innerBorder: 0,
	navType:'both',
	controlsPos:'br',
	showNavOverlay:true,
	enableWrap: true,
	navOverlayWidth:50,
	navOverlayPos:50,
	delay: 10,
	preloadLimit: 1,
},

// Option settings can be assigned based on floatbox content type.
// The syntax of typeOptions is different than the object code above.
// Each type is assigned an option string formatted the same as
// the options placed in a link's data-fb-options (or rev) attribute.
// example - iframe: "colorTheme:blue showNewWindow:true",
// Javascript Object Notation can be used instead of the option string.

typeOptions: {
  image: "",
  // html settings apply to all 5 html sub-types that follow
  html: "",
	iframe: "",
	inline: "",
	ajax: "",
	direct: "",
	pdf: "width:80% height:95%",
  // media settings apply to the 2 sub-types as well
  media: "",
	video: "",
	flash: ""
},

// Settings can propogate to groups of anchors by assigning the anchors a class
// and associating that class name with a string or object of options here.
// The syntax is the same as for typeOptions above.

classOptions: {
  alt: {
	autoFit: false,
	boxCornerRadius: 8,
	shadowType: "hybrid",
	showClose: false,
	showOuterClose: true,
	captionPos: "bc",
	caption2Pos: "tl",
	infoLinkPos: "tl",
	printLinkPos: "tl",
	newWindowLinkPos: "tl",
	controlsPos: "tr",
	centerNav: true,
	doAnimations:false
  },
  transparent: {
	autoFit: false,
	boxColor: "transparent",
	contentBackgroundColor: "transparent",
	boxRoundCorners: "none",
	shadowType: "none",
	showOuterClose: true,
	showClose: false,
	overlayOpacity: 75,
	outerBorder: 2,
	innerBorder: 0,
	zoomBorder: 0,
	doAnimations:false
  },
  naked: {
	autoFit: false,
	boxRoundCorners: "none",
	showOuterClose: true,
	showClose: false,
	inFrameResize: false,
	showItemNumber: false,
	navType: "overlay",
	caption: null,
	outerBorder: 0,
	innerBorder: 0,
	padding: 0,
	panelPadding: 0,
	zoomBorder: 0,
	doAnimations:false
  },
  childBox: {  // good for second boxes such as an Info... box
	autoFit: false,
	boxCornerRadius: 6,
	shadowSize: 8,
	padding: 18,
	overlayOpacity: 45,
	resizeTime: 0.3,
	fadeTime: 0,
	transitionTime: 0.3,
	overlayFadeTime: 0.3,
	doAnimations:false
  },
  fbTooltip: {  // target enhanced tooltips with options set here
	fadeTime: 0.01,
	doAnimations:false
  },
  fbContext: {  // target context boxes with options set here
	fadeTime: 0,
	doAnimations:false
  }
},

// END OF EDITABLE CONTENT
// ***********************
ready: true};
