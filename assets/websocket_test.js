window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        websocket_test: function(clicks) {

            console.log("Run Recording Function")

            const ws = new WebSocket(`ws://${window.location.host}/ws`);

            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            recognition.continuous = true;

            ws.onmessage = function (event) {
                console.log(event.data);
            };

            //let wav = require('node-wav');

            function audioBufferToWav (buffer, opt) {
              opt = opt || {}

              var numChannels = buffer.numberOfChannels
              var sampleRate = buffer.sampleRate
              var format = opt.float32 ? 3 : 1
              var bitDepth = format === 3 ? 32 : 16

              var result
              if (numChannels === 2) {
                result = interleave(buffer.getChannelData(0), buffer.getChannelData(1))
              } else {
                result = buffer.getChannelData(0)
              }

              return encodeWAV(result, format, sampleRate, numChannels, bitDepth)
            }

            function encodeWAV (samples, format, sampleRate, numChannels, bitDepth) {
              var bytesPerSample = bitDepth / 8
              var blockAlign = numChannels * bytesPerSample

              var buffer = new ArrayBuffer(44 + samples.length * bytesPerSample)
              var view = new DataView(buffer)

              /* RIFF identifier */
              writeString(view, 0, 'RIFF')
              /* RIFF chunk length */
              view.setUint32(4, 36 + samples.length * bytesPerSample, true)
              /* RIFF type */
              writeString(view, 8, 'WAVE')
              /* format chunk identifier */
              writeString(view, 12, 'fmt ')
              /* format chunk length */
              view.setUint32(16, 16, true)
              /* sample format (raw) */
              view.setUint16(20, format, true)
              /* channel count */
              view.setUint16(22, numChannels, true)
              /* sample rate */
              view.setUint32(24, sampleRate, true)
              /* byte rate (sample rate * block align) */
              view.setUint32(28, sampleRate * blockAlign, true)
              /* block align (channel count * bytes per sample) */
              view.setUint16(32, blockAlign, true)
              /* bits per sample */
              view.setUint16(34, bitDepth, true)
              /* data chunk identifier */
              writeString(view, 36, 'data')
              /* data chunk length */
              view.setUint32(40, samples.length * bytesPerSample, true)
              if (format === 1) { // Raw PCM
                floatTo16BitPCM(view, 44, samples)
              } else {
                writeFloat32(view, 44, samples)
              }

              return buffer
            }

            function interleave (inputL, inputR) {
              var length = inputL.length + inputR.length
              var result = new Float32Array(length)

              var index = 0
              var inputIndex = 0

              while (index < length) {
                result[index++] = inputL[inputIndex]
                result[index++] = inputR[inputIndex]
                inputIndex++
              }
              return result
            }

            function writeFloat32 (output, offset, input) {
              for (var i = 0; i < input.length; i++, offset += 4) {
                output.setFloat32(offset, input[i], true)
              }
            }

            function floatTo16BitPCM (output, offset, input) {
              for (var i = 0; i < input.length; i++, offset += 2) {
                var s = Math.max(-1, Math.min(1, input[i]))
                output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
              }
            }

            function writeString (view, offset, string) {
              for (var i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i))
              }
            }

            async function GetAudio(clicks) {

                console.log("Run Audio getter")

                const audioContext = new AudioContext();

                var recognition = new webkitSpeechRecognition();

                // Look up the frame rate, maybe it's 16000Hz
                // Should be a mono sound

                navigator.mediaDevices.getUserMedia({ audio: true })
                      .then(stream => {

                        const mediaRecorder = new MediaRecorder(stream);
                        mediaRecorder.start();

                        const audioChunks = [];

                        mediaRecorder.addEventListener("dataavailable", event => {
                          audioChunks.push(event.data);
                        });

                        mediaRecorder.addEventListener("stop", () => {
                          const audioBlob = new Blob(audioChunks, { 'type' : 'audio/wav' });
                          console.log(typeof audioBlob)
                          const thing = new Response(audioBlob).arrayBuffer().then(buffer => 
                            {
                                audioContext.decodeAudioData(buffer, (audioBuffer) => {
                                    var wav = audioBufferToWav(audioBuffer);
                                    console.log(wav);
                                    ws.send(wav);
                                });

                                //var view = new DataView(buffer);
                                //buffer.getChannelData(0);
                                //console.log(view)
                                //view.setUint32(4, 44 + buffer.length * 2, true);
                                //ws.send(buffer);
                            }
                            );
                          //console.log(audioBlob)
                          const audioUrl = URL.createObjectURL(audioBlob);
                          const audio = new Audio(audioUrl);
                          //audio.play();

                          //console.log(typeof audioChunks);
                          //console.log(audioUrl);
                          //ws.send(audioBlob);
                        });

                        //buffer = wrapRecorder(audioChunks);
                        //console.log(buffer);

                        //var view = new DataView(buffer);

                        setTimeout(() => {
                          mediaRecorder.stop();
                        }, 3000);
                      }); 
            };

            GetAudio(clicks);

        }
    }
});