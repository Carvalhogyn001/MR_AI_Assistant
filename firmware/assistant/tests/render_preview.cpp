#include <Arduino_GFX_Library.h>
#include "face_renderer.h"
#include <algorithm>
#include <fstream>
#include <cstring>
#include <iostream>

namespace preview {
std::ostringstream shapes;
std::vector<std::string> labels;
}
using namespace mr_robot;
namespace mr_robot {
const char* name(Face f) { return f==Face::Classic?"classic":f==Face::Pixel?"pixel":"orbit"; }
const char* name(HostProvider p) { return p==HostProvider::Gemini?"gemini":p==HostProvider::Compatible?"compatible":p==HostProvider::Ollama?"ollama":"mock"; }
}
bool has(const char* label) { return std::find(preview::labels.begin(),preview::labels.end(),label)!=preview::labels.end(); }
int main(int argc,char** argv) {
  assert(argc==2);
  assert(beginDisplay(96));
  std::ofstream out(argv[1]);
  assert(out);
  out << "<svg xmlns='http://www.w3.org/2000/svg' width='1466' height='2126' viewBox='0 0 1466 2126'>"
      << "<rect width='100%' height='100%' fill='#f4f3ef'/><g fill='#253943' font-family='Arial,sans-serif'>"
      << "<text x='30' y='44' font-size='25'>MR. Robot / device interface</text>"
      << "<text x='30' y='73' font-size='16'>Actual renderer geometry and bitmap type. Host preview; physical panel acceptance is separate.</text></g>";
  const char* names[] = {"Idle", "Ready", "Wake listening", "Listening", "Thinking", "Receiving", "Speaking", "Stopped / recovery", "Host caption", "Mic test ready", "Mic diagnostic", "Orbit / curious"};
  const VoicePhase phases[] = {VoicePhase::Idle,VoicePhase::Ready,VoicePhase::Wake,VoicePhase::Recording,
      VoicePhase::Thinking,VoicePhase::Receiving,VoicePhase::Speaking,VoicePhase::Error};
  for (int i=0;i<12;++i) {
    AppState state; state.touchReady=true;
    if (i<8) state.voicePhase=phases[i];
    state.voiceStreaming=true;
    if (i==2 || i==3 || i==10) state.microphoneActive=true;
    if (i==8) { std::strcpy(state.caption,"Your reply stays easy to read. Full conversation and settings are available in Control Room."); state.captionProvider=HostProvider::Gemini; }
    if (i==9) state.microphoneArmed=true;
    if (i==10) { state.micRms[0]=119; state.micRms[2]=121; }
    if (i==11) { state.face=Face::Orbit; state.expression=Expression::Curious; }
    renderFace(state,1050);
    if (i==0) assert(has("MIC OFF / VOICE NOT ARMED"));
    if (i==1) assert(has("MIC OFF / VOICE ARMED"));
    if (i==2) assert(has("MIC ON / OR TAP TO TALK"));
    if (i==3) assert(has("LISTENING") && has("TAP TO CANCEL"));
    if (i==7) assert(has("VOICE STOPPED") && has("CHECK CONTROL ROOM") && !has("TAP TO CANCEL"));
    const int x=20+(i%3)*482, y=108+(i/3)*500;
    out << "<g transform='translate("<<x<<','<<y<<")'>"<<preview::shapes.str()<<"</g>"
        << "<text x='"<<x+233<<"' y='"<<y+485<<"' text-anchor='middle' fill='#253943' font-family='Arial,sans-serif' font-size='18'>"<<names[i]<<"</text>";
  }
  out << "</svg>";
  // Privacy priority and worst-case caption layout are behavioral checks,
  // not a second hand-written implementation of the new artwork.
  AppState state; state.voicePhase=VoicePhase::Error; state.microphoneActive=true;
  std::strcpy(state.caption,"This stale caption must never hide active microphone capture.");
  renderFace(state,1050);
  assert(has("MIC LEVEL TEST") && has("MIC ON / LOCAL TEST") && !has("VOICE STOPPED"));
  state={}; state.voicePhase=VoicePhase::Recording; state.voiceStreaming=false; state.micFrames=32000;
  renderFace(state,1050);
  assert(has("6 SECONDS LEFT") && has("MIC ON / GEMINI VIA MAC"));
  state={}; std::memset(state.caption,'W',kMaxCaptionBytes); state.captionProvider=HostProvider::Compatible;
  renderFace(state,1050);
  assert(has("compatible / MAC / MIC OFF"));
  state = {};
  state.captionProvider = HostProvider::Ollama;
  std::memset(state.caption, 'W', kMaxCaptionBytes);
  for (state.captionPage = 0; state.captionPage < 5; ++state.captionPage) {
    renderFace(state,1050);
    assert(!has("OLLAMA REPLY") && !has("MIC OFF / LOCAL ON MAC"));
  }
  for (const auto face : {Face::Classic,Face::Pixel,Face::Orbit}) for (const auto expression : {Expression::Neutral,Expression::Happy,Expression::Curious,Expression::Sleepy,Expression::Surprised,Expression::Wink,Expression::Excited,Expression::Concerned,Expression::Squint,Expression::Blush,Expression::Dizzy}) {
    state={}; state.face=face; state.expression=expression;
    renderFace(state,0); renderFace(state,1050);
  }
  state = {};
  state.screen = Screen::Settings;
  renderFace(state, 1050);
  assert(has("SETTINGS") && has("TAP LEFT OR RIGHT TO ADJUST"));
  state.screen = Screen::Gallery;
  state.voicePhase = VoicePhase::Wake;
  state.microphoneActive = true;
  renderFace(state, 1050);
  assert(has("GALLERY") && has("MIC ON / SWIPE FOR SCREENS"));
  state.voicePhase = VoicePhase::Recording;
  renderFace(state, 1050);
  assert(has("LISTENING") && !has("GALLERY"));
  state = {};
  state.hostActivity = HostActivity::Drawing;
  renderFace(state, 1050);
  assert(has("DRAWING IMAGE"));
  state.hostActivity = HostActivity::Error;
  renderFace(state, 1050);
  assert(has("REQUEST STOPPED"));
  std::cout << "PASS: actual renderer state labels, microphone priority, circular text bounds, captions and 33 face/expression combinations and swipe screen priorities\n";
}
