#import <Cocoa/Cocoa.h>
#import <AppKit/AppKit.h>
#import <Carbon/Carbon.h>

@interface TransparentWindow : NSWindow
@property (nonatomic) NSPoint initialMouseLocation;
@end

@implementation TransparentWindow

// Diese Methode wird aufgerufen, wenn die Maus gedrückt wird
- (void)mouseDown:(NSEvent *)event {
    // Speichere die Mausposition, wenn der Benutzer das Fenster an einer beliebigen Stelle zieht
    self.initialMouseLocation = [event locationInWindow];
}

// Diese Methode wird aufgerufen, wenn die Maus bewegt wird
- (void)mouseDragged:(NSEvent *)event {
    // Berechne die Verschiebung der Maus
    NSPoint currentMouseLocation = [event locationInWindow];
    NSPoint delta = NSMakePoint(currentMouseLocation.x - self.initialMouseLocation.x, currentMouseLocation.y - self.initialMouseLocation.y);

    // Berechne die neue Position des Fensters
    NSRect newFrame = self.frame;
    newFrame.origin.x += delta.x;
    newFrame.origin.y += delta.y;

    // Setze das Fenster auf die neue Position
    [self setFrame:newFrame display:YES];

    // Aktualisiere die ursprüngliche Mausposition
    self.initialMouseLocation = currentMouseLocation;
}

@end

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property NSStatusItem *statusItem;
@property TransparentWindow *window;
@property (nonatomic) NSPoint lastMouseLocation;  // Zum Speichern der letzten Mausposition
@property NSImageView *imageView;
@property NSArray<NSImage *> *frames;
@property NSInteger currentFrame;
@property NSTimer *timer;
@property NSImage *frameIdle;
@property NSImage *frameLeft;
@property NSImage *frameBoth;
@property NSImage *frameRight;
@property NSDate *lastKeyDownTime;
@property NSTimeInterval doubleKeyThreshold; // z. B. 0.15 Sekunden
@property BOOL isLeft;
@end

@implementation AppDelegate

- (void)setClickThrough:(BOOL)enabled {
    [self.window setIgnoresMouseEvents:enabled];
}

- (void)toggleClickThrough:(id)sender {
    BOOL current = [self.window ignoresMouseEvents];
    [self setClickThrough:!current];
}

- (void)toggleWindowVisibility:(id)sender {
    if ([self.window isVisible]) {
        [self.window orderOut:nil];
    } else {
        [self.window makeKeyAndOrderFront:nil];
    }
}
- (void)triggerBongoHitSingle {
    [self stopIdleAnimation];

    NSImage *hitFrame = self.isLeft ? self.frameLeft : self.frameRight;
    self.isLeft = !self.isLeft;

    self.imageView.image = hitFrame;

    // Nach kurzer Zeit zurück zu Idle
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [self startIdleAnimation];
    });
}

- (void)triggerBongoHitBoth {
    [self stopIdleAnimation];

    self.imageView.image = self.frameBoth;

    // Nach kurzer Zeit zurück zu Idle
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [self startIdleAnimation];
    });
}

- (void)startIdleAnimation {
    if (self.timer) return;

    //self.idleIndex = 0;
    // Timer für Animation
    self.timer = [NSTimer scheduledTimerWithTimeInterval:0.1 target:self selector:@selector(updateFrame) userInfo:nil repeats:YES];
}

- (void)stopIdleAnimation {
    [self.timer invalidate];
    self.timer = nil;
}
- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Lade Frames 
    NSString *myExePath = NSProcessInfo.processInfo.arguments[0];
    NSString *exeDir = [myExePath stringByDeletingLastPathComponent];
    NSString *framesDir = [exeDir stringByAppendingPathComponent:@"frames"];

    NSMutableArray *frameImages = [NSMutableArray array];
    for (int i = 0; i < 3; i++) {
        NSString *framePath = [framesDir stringByAppendingPathComponent:[NSString stringWithFormat:@"frame_%03d.png", i]];
        NSImage *img = [[NSImage alloc] initWithContentsOfFile:framePath];
        if (img) [frameImages addObject:img];
    }

    self.frames = frameImages;
    self.currentFrame = 0;

    self.frameLeft = [[NSImage alloc] initWithContentsOfFile:[framesDir stringByAppendingPathComponent:@"hit_left.png"]];
    self.frameRight = [[NSImage alloc] initWithContentsOfFile:[framesDir stringByAppendingPathComponent:@"hit_right.png"]];
    self.frameBoth = [[NSImage alloc] initWithContentsOfFile:[framesDir stringByAppendingPathComponent:@"hit_both.png"]];

    //self.imageView.image = self.frameIdle;
    self.isLeft = YES;
    self.doubleKeyThreshold = 0.05;
    self.lastKeyDownTime = nil;

    // Fenster erstellen
    NSRect frame = NSMakeRect(100, 100, 300, 300);
    self.window = [[TransparentWindow alloc]
                   initWithContentRect:frame
                   styleMask:NSWindowStyleMaskBorderless
                   backing:NSBackingStoreBuffered
                   defer:NO];

    [self.window setBackgroundColor:[NSColor clearColor]];
    [self.window setOpaque:NO];
    [self.window setLevel:NSStatusWindowLevel + 1];
    [self.window setIgnoresMouseEvents:NO]; // Stellen Sie sicher, dass das Fenster Mausereignisse verarbeitet


    // Bildansicht
    self.imageView = [[NSImageView alloc] initWithFrame:frame];
    [self.imageView setImageScaling:NSImageScaleAxesIndependently];
    [[self.window contentView] addSubview:self.imageView];

    [self.window makeKeyAndOrderFront:nil];
    [self startIdleAnimation];
    // Tray-Icon
    self.statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSVariableStatusItemLength];
    NSImage *trayIcon = [NSImage imageNamed:NSImageNameInfo]; // oder eigenes Icon
    [trayIcon setTemplate:YES];
    self.statusItem.button.image = trayIcon;

    // Menubar
    NSMenu *menu = [[NSMenu alloc] init];
    [menu addItemWithTitle:@"Toggle Visibility" action:@selector(toggleWindowVisibility:) keyEquivalent:@"v"];
    [menu addItemWithTitle:@"Toggle Click-Through" action:@selector(toggleClickThrough:) keyEquivalent:@"c"];
    [menu addItem:[NSMenuItem separatorItem]];
    [menu addItemWithTitle:@"Quit" action:@selector(terminate:) keyEquivalent:@"q"];
    self.statusItem.menu = menu;

// Drag-to-move
NSTrackingArea *tracking = [[NSTrackingArea alloc] initWithRect:self.window.contentView.bounds
                                                         options:NSTrackingMouseMoved | NSTrackingActiveInKeyWindow
                                                           owner:self
                                                        userInfo:nil];
[self.window.contentView addTrackingArea:tracking];

// Tracking Area in der windowDidLoad oder applicationDidFinishLaunching hinzufügen

    // Hide with cmd + shift + b
    [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown handler:^NSEvent* (NSEvent *event) {
    if ((event.modifierFlags & NSEventModifierFlagCommand) &&
        (event.modifierFlags & NSEventModifierFlagShift) &&
        [[event charactersIgnoringModifiers] isEqualToString:@"B"]) {

        BOOL isVisible = [self.window isVisible];
        if (isVisible) {
            [self.window orderOut:nil];
        } else {
            [self.window makeKeyAndOrderFront:nil];
        }
        return nil; // Block das Event
    }
    return event;
    }];

    // Old Global Listener
    /* NSEventMaskKeyDown handler:^(NSEvent *event) {
    [self triggerBongoHit];
    }];*/

    // Global Key Event Listener with Both Paws!
    [NSEvent addGlobalMonitorForEventsMatchingMask:NSEventMaskKeyDown handler:^(NSEvent *event) {
    NSDate *now = [NSDate date];
    if (self.lastKeyDownTime && [now timeIntervalSinceDate:self.lastKeyDownTime] < self.doubleKeyThreshold) {
        NSLog(@"Double key press detected → BOTH paws!");
        [self triggerBongoHitBoth];
        self.lastKeyDownTime = nil; // zurücksetzen
    } else {
        self.lastKeyDownTime = now;
        [self triggerBongoHitSingle];
    }
    }];
}

- (void)updateFrame {
    if (self.frames.count == 0) return;
    self.imageView.image = self.frames[self.currentFrame];
    self.currentFrame = (self.currentFrame + 1) % self.frames.count;
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        [NSApplication sharedApplication];
        AppDelegate *delegate = [[AppDelegate alloc] init];
        [NSApp setDelegate:delegate];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
        return NSApplicationMain(argc, argv);
    }
}
