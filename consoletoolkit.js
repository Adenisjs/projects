snake: () => {
      const win = createWindow('snake', '🐍 Snake Game', `
        <div style="text-align:center;">
          <div style="font-size:24px;font-weight:700;margin-bottom:15px;">Score: <span id="snake-score">0</span></div>
          <canvas id="snake-canvas" width="300" height="300" style="border:3px solid #333;border-radius:8px;background:#f0f0f0;"></canvas>
          <button class="tw-btn tw-btn-primary" id="snake-restart" style="margin-top:15px;">🔄 Restart Game</button>
          <div style="font-size:12px;color:#718096;margin-top:10px;">Use arrow keys to play</div>
        </div>
      `, '360px');

      const canvas = win.querySelector('#snake-canvas');
      const ctx = canvas.getContext('2d');
      const scoreEl = win.querySelector('#snake-score');
      const restartBtn = win.querySelector('#snake-restart');

      const gridSize = 15;
      const tileSize = 20;
      let snake = [{x: 7, y: 7}];
      let dir = {x: 1, y: 0};
      let food = {x: 10, y: 10};
      let score = 0;
      let gameLoop;

      function draw() {
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, 300, 300);

        ctx.fillStyle = '#48bb78';
        snake.forEach(s => ctx.fillRect(s.x * tileSize, s.y * tileSize, tileSize - 2, tileSize - 2));

        ctx.fillStyle = '#f56565';
        ctx.fillRect(food.x * tileSize, food.y * tileSize, tileSize - 2, tileSize - 2);
      }

      function update() {
        const head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};

        if (head.x < 0 || head.x >= gridSize || head.y < 0 || head.y >= gridSize || snake.some(s => s.x === head.x && s.y === head.y)) {
          clearInterval(gameLoop);
          alert('Game Over! Score: ' + score);
          return;
        }

        snake.unshift(head);

        if (head.x === food.x && head.y === food.y) {
          score++;
          scoreEl.textContent = score;
          food = {x: Math.floor(Math.random() * gridSize), y: Math.floor(Math.random() * gridSize)};
        } else {
          snake.pop();
        }

        draw();
      }

      document.addEventListener('keydown', (e) => {
        if (!win.parentNode) return;
        if (e.key === 'ArrowUp' && dir.y === 0) dir = {x: 0, y: -1};
        if (e.key === 'ArrowDown' && dir.y === 0) dir = {x: 0, y: 1};
        if (e.key === 'ArrowLeft' && dir.x === 0) dir = {x: -1, y: 0};
        if (e.key === 'ArrowRight' && dir.x === 0) dir = {x: 1, y: 0};
      });

      function start() {
        snake = [{x: 7, y: 7}];
        dir = {x: 1, y: 0};
        score = 0;
        scoreEl.textContent = '0';
        food = {x: 10, y: 10};
        clearInterval(gameLoop);
        gameLoop = setInterval(update, 150);
        draw();
      }

      restartBtn.onclick = start;
      start();
    },

    inspector: () => {
      const overlay = document.createElement('div');
      overlay.id = 'inspector-overlay';
      overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:999996;';
      
      const box = document.createElement('div');
      box.style.cssText = 'position:absolute;border:2px solid #667eea;background:rgba(102,126,234,0.1);pointer-events:none;box-shadow:0 0 0 9999px rgba(0,0,0,0.3);';
      overlay.appendChild(box);
      
      const label = document.createElement('div');
      label.style.cssText = 'position:absolute;background:#667eea;color:white;padding:6px 12px;font-size:12px;border-radius:6px;pointer-events:none;font-family:monospace;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,0.3);';
      overlay.appendChild(label);

      const info = document.createElement('div');
      info.style.cssText = 'position:fixed;bottom:20px;left:20px;background:rgba(30,30,30,0.95);color:white;padding:15px 20px;border-radius:12px;font-family:monospace;font-size:12px;max-width:400px;backdrop-filter:blur(10px);box-shadow:0 4px 20px rgba(0,0,0,0.5);';
      info.innerHTML = '<div style="font-weight:700;margin-bottom:8px;">🔍 Inspector Active</div><div id="inspector-info">Hover over elements...</div><div style="margin-top:10px;font-size:11px;opacity:0.7;">Press ESC to exit</div>';
      overlay.appendChild(info);
      
      document.body.appendChild(overlay);
      
      let lastEl = null;
      const infoDiv = info.querySelector('#inspector-info');
      
      const moveHandler = (e) => {
        const el = document.elementFromPoint(e.clientX, e.clientY);
        if (el && el !== lastEl && !el.closest('#inspector-overlay') && !el.closest('.tw')) {
          lastEl = el;
          const rect = el.getBoundingClientRect();
          box.style.left = rect.left + 'px';
          box.style.top = rect.top + 'px';
          box.style.width = rect.width + 'px';
          box.style.height = rect.height + 'px';
          
          const tag = el.tagName.toLowerCase();
          const id = el.id ? `#${el.id}` : '';
          const cls = el.className ? `.${el.className.toString().split(' ')[0]}` : '';
          const styles = window.getComputedStyle(el);
          
          label.textContent = `${tag}${id}${cls}`;
          label.style.left = rect.left + 'px';
          label.style.top = Math.max(0, rect.top - 30) + 'px';
          
          infoDiv.innerHTML = `
            <strong>${tag}${id}${cls}</strong><br>
            Size: ${Math.round(rect.width)} × ${Math.round(rect.height)}px<br>
            Position: ${Math.round(rect.left)}, ${Math.round(rect.top)}<br>
            Color: ${styles.color}<br>
            Background: ${styles.backgroundColor}<br>
            Font: ${styles.fontSize} ${styles.fontFamily.split(',')[0]}
          `;
        }
      };

      const keyHandler = (e) => {
        if (e.key === 'Escape') {
          overlay.remove();
          document.removeEventListener('mousemove', moveHandler);
          document.removeEventListener('keydown', keyHandler);
        }
      };
      
      document.addEventListener('mousemove', moveHandler);
      document.addEventListener('keydown', keyHandler);
    },

    textreplace: () => {
      const win = createWindow('textreplace', '✏️ Text Replacer', `
        <label class="tw-label">Find Text:</label>
        <input type="text" class="tw-input" id="tr-find" placeholder="Enter text to find...">
        
        <label class="tw-label">Replace With:</label>
        <input type="text" class="tw-input" id="tr-replace" placeholder="Enter replacement...">
        
        <div style="display:flex;gap:8px;align-items:center;margin:10px 0;">
          <input type="checkbox" id="tr-case" style="width:auto;">
          <label for="tr-case" style="margin:0;font-size:13px;color:#4a5568;">Case sensitive</label>
        </div>
        
        <button class="tw-btn tw-btn-primary" id="tr-replace-btn">🔄 Replace All</button>
        <button class="tw-btn tw-btn-secondary" id="tr-highlight-btn">🔍 Highlight Matches</button>
        <button class="tw-btn tw-btn-danger" id="tr-undo-btn">↩️ Undo Changes</button>
        
        <div id="tr-status" style="margin-top:15px;padding:12px;background:#f7fafc;border-radius:8px;text-align:center;font-size:13px;color:#4a5568;"></div>
      `, '450px');

      const findInput = win.querySelector('#tr-find');
      const replaceInput = win.querySelector('#tr-replace');
      const caseCheck = win.querySelector('#tr-case');
      const replaceBtn = win.querySelector('#tr-replace-btn');
      const highlightBtn = win.querySelector('#tr-highlight-btn');
      const undoBtn = win.querySelector('#tr-undo-btn');
      const status = win.querySelector('#tr-status');

      let originalHTML = document.body.innerHTML;

      replaceBtn.onclick = () => {
        const find = findInput.value;
        if (!find) return status.textContent = '⚠️ Enter text to find!';
        
        originalHTML = document.body.innerHTML;
        const replace = replaceInput.value;
        const flags = caseCheck.checked ? 'g' : 'gi';
        
        const walker = document.createTreeWalker(
          document.body,
          NodeFilter.SHOW_TEXT,
          null,
          false
        );

        let count = 0;
        const nodesToReplace = [];
        
        while (walker.nextNode()) {
          const node = walker.currentNode;
          if (node.parentElement.closest('.tw, #aden-toolkit')) continue;
          
          const regex = new RegExp(find.replace(/[.*+?^${}()|[\]\\]/g, '\\'), flags);
          if (regex.test(node.textContent)) {
            nodesToReplace.push(node);
          }
        }

        nodesToReplace.forEach(node => {
          const regex = new RegExp(find.replace(/[.*+?^${}()|[\]\\]/g, '\\'), flags);
          const matches = node.textContent.match(regex);
          if (matches) count += matches.length;
          node.textContent = node.textContent.replace(regex, replace);
        });

        status.textContent = `✓ Replaced ${count} occurrence(s)`;
      };

      highlightBtn.onclick = () => {
        const find = findInput.value;
        if (!find) return status.textContent = '⚠️ Enter text to find!';
        
        const flags = caseCheck.checked ? 'g' : 'gi';
        const regex = new RegExp(`(${find.replace(/[.*+?^${}()|[\]\\]/g, '\\')})`, flags);
        
        const walker = document.createTreeWalker(
          document.body,
          NodeFilter.SHOW_TEXT,
          null,
          false
        );

        let count = 0;
        const nodesToHighlight = [];
        
        while (walker.nextNode()) {
          const node = walker.currentNode;
          if (node.parentElement.closest('.tw, #aden-toolkit')) continue;
          if (regex.test(node.textContent)) {
            nodesToHighlight.push(node);
          }
        }

        nodesToHighlight.forEach(node => {
          const matches = node.textContent.match(regex);
          if (matches) count += matches.length;
          
          const span = document.createElement('span');
          span.innerHTML = node.textContent.replace(regex, '<mark style="background:#ffd700;padding:2px 4px;border-radius:3px;">$1</mark>');
          node.parentNode.replaceChild(span, node);
        });

        status.textContent = `🔍 Highlighted ${count} match(es)`;
      };

      undoBtn.onclick = () => {
        document.body.innerHTML = originalHTML;
        status.textContent = '↩️ Changes undone';
        setTimeout(() => {
          const newWin = createWindow('textreplace', '✏️ Text Replacer', win.querySelector('.tw-body').innerHTML, '450px');
        }, 100);
      };

      status.textContent = 'Ready to replace text on this page';
    },

    typing: () => {
      const sentences = [
        'The quick brown fox jumps over the lazy dog.',
        'Pack my box with five dozen liquor jugs.',
        'How vexingly quick daft zebras jump!',
        'The five boxing wizards jump quickly.',
        'Sphinx of black quartz, judge my vow.',
        'Two driven jocks help fax my big quiz.',
        'Quick zephyrs blow, vexing daft Jim.',
      ];

      const win = createWindow('typing', '⌨️ Typing Test', `
        <div style="text-align:center;">
          <div style="display:flex;justify-content:space-around;margin-bottom:20px;">
            <div>
              <div style="font-size:32px;font-weight:900;color:#667eea;" id="typing-wpm">0</div>
              <div style="font-size:12px;color:#718096;">WPM</div>
            </div>
            <div>
              <div style="font-size:32px;font-weight:900;color:#48bb78;" id="typing-accuracy">100</div>
              <div style="font-size:12px;color:#718096;">Accuracy %</div>
            </div>
            <div>
              <div style="font-size:32px;font-weight:900;color:#f6ad55;" id="typing-time">60</div>
              <div style="font-size:12px;color:#718096;">Seconds</div>
            </div>
          </div>
          
          <div id="typing-text" style="font-size:20px;line-height:1.8;padding:20px;background:#f7fafc;border-radius:12px;margin-bottom:20px;min-height:100px;font-family:monospace;"></div>
          
          <textarea id="typing-input" class="tw-input" rows="4" placeholder="Click here and start typing..." style="font-size:18px;font-family:monospace;"></textarea>
          
          <button class="tw-btn tw-btn-primary" id="typing-restart">🔄 New Test</button>
        </div>
      `, '600px');

      const wpmEl = win.querySelector('#typing-wpm');
      const accEl = win.querySelector('#typing-accuracy');
      const timeEl = win.querySelector('#typing-time');
      const textEl = win.querySelector('#typing-text');
      const input = win.querySelector('#typing-input');
      const restartBtn = win.querySelector('#typing-restart');

      let currentText = '';
      let startTime = null;
      let timeLeft = 60;
      let timerInterval = null;
      let errors = 0;

      function newTest() {
        currentText = sentences[Math.floor(Math.random() * sentences.length)];
        textEl.textContent = currentText;
        input.value = '';
        input.disabled = false;
        startTime = null;
        timeLeft = 60;
        errors = 0;
        timeEl.textContent = '60';
        wpmEl.textContent = '0';
        accEl.textContent = '100';
        clearInterval(timerInterval);
      }

      input.oninput = () => {
        if (!startTime) {
          startTime = Date.now();
          timerInterval = setInterval(() => {
            timeLeft--;
            timeEl.textContent = timeLeft;
            if (timeLeft <= 0) {
              clearInterval(timerInterval);
              input.disabled = true;
              alert(`Test Complete!\nWPM: ${wpmEl.textContent}\nAccuracy: ${accEl.textContent}%`);
            }
          }, 1000);
        }

        const typed = input.value;
        const words = typed.trim().split(/\s+/).length;
        const minutes = (Date.now() - startTime) / 60000;
        const wpm = Math.round(words / minutes) || 0;
        wpmEl.textContent = wpm;

        // Calculate accuracy
        errors = 0;
        for (let i = 0; i < typed.length; i++) {
          if (typed[i] !== currentText[i]) errors++;
        }
        const accuracy = Math.round(((typed.length - errors) / typed.length) * 100) || 100;
        accEl.textContent = accuracy;

        // Highlight text
        let html = '';
        for (let i = 0; i < currentText.length; i++) {
          const char = currentText[i];
          if (i < typed.length) {
            if (typed[i] === char) {
              html += `<span style="color:#48bb78;">${char}</span>`;
            } else {
              html += `<span style="color:#f56565;background:#ffe0e0;">${char}</span>`;
            }
          } else if (i === typed.length) {
            html += `<span style="background:#ffd700;">${char}</span>`;
          } else {
            html += char;
          }
        }
        textEl.innerHTML = html;

        if (typed === currentText) {
          clearInterval(timerInterval);
          input.disabled = true;
          setTimeout(() => {
            alert(`Perfect! Test Complete!\nWPM: ${wpm}\nAccuracy: ${accuracy}%\nTime: ${60 - timeLeft}s`);
          }, 100);
        }
      };

      restartBtn.onclick = newTest;
      newTest();
    },

    memory: () => {
      const emojis = ['🍎', '🍌', '🍇', '🍊', '🍓', '🍉', '🍒', '🥝'];
      
      const win = createWindow('memory', '🎴 Memory Game', `
        <div style="text-align:center;">
          <div style="display:flex;justify-content:space-around;margin-bottom:20px;">
            <div>
              <div style="font-size:28px;font-weight:900;color:#667eea;" id="mem-moves">0</div>
              <div style="font-size:12px;color:#718096;">Moves</div>
            </div>
            <div>
              <div style="font-size:28px;font-weight:900;color:#48bb78;" id="mem-matches">0</div>
              <div style="font-size:12px;color:#718096;">Matches</div>
            </div>
            <div>
              <div style="font-size:28px;font-weight:900;color:#f6ad55;" id="mem-time">0</div>
              <div style="font-size:12px;color:#718096;">Seconds</div>
            </div>
          </div>
          
          <div id="mem-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;"></div>
          
          <button class="tw-btn tw-btn-primary" id="mem-restart">🔄 New Game</button>
        </div>
      `, '450px');

      const movesEl = win.querySelector('#mem-moves');
      const matchesEl = win.querySelector('#mem-matches');
      const timeEl = win.querySelector('#mem-time');
      const grid = win.querySelector('#mem-grid');
      const restartBtn = win.querySelector('#mem-restart');

      let cards = [];
      let flipped = [];
      let matched = [];
      let moves = 0;
      let matchCount = 0;
      let time = 0;
      let timer = null;
      let canFlip = true;

      function createGame() {
        const gameEmojis = [...emojis, ...emojis];
        gameEmojis.sort(() => Math.random() - 0.5);
        
        cards = gameEmojis;
        flipped = [];
        matched = [];
        moves = 0;
        matchCount = 0;
        time = 0;
        movesEl.textContent = '0';
        matchesEl.textContent = '0';
        timeEl.textContent = '0';
        clearInterval(timer);
        canFlip = true;

        grid.innerHTML = gameEmojis.map((emoji, i) => `
          <div class="mem-card" data-index="${i}" style="
            width:100%;
            aspect-ratio:1;
            background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius:12px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:36px;
            cursor:pointer;
            transition:all 0.3s;
            user-select:none;
          ">?</div>
        `).join('');

        grid.querySelectorAll('.mem-card').forEach(card => {
          card.onclick = () => flipCard(parseInt(card.dataset.index));
        });
      }

      function flipCard(index) {
        if (!canFlip || flipped.includes(index) || matched.includes(index)) return;
        
        if (!timer) {
          timer = setInterval(() => {
            time++;
            timeEl.textContent = time;
          }, 1000);
        }

        const card = grid.children[index];
        card.textContent = cards[index];
        card.style.background = 'white';
        card.style.transform = 'scale(1.05)';
        
        flipped.push(index);

        if (flipped.length === 2) {
          moves++;
          movesEl.textContent = moves;
          canFlip = false;

          setTimeout(() => {
            const [first, second] = flipped;
            if (cards[first] === cards[second]) {
              matched.push(first, second);
              matchCount++;
              matchesEl.textContent = matchCount;
              
              if (matched.length === cards.length) {
                clearInterval(timer);
                setTimeout(() => {
                  alert(`🎉 You Won!\nMoves: ${moves}\nTime: ${time}s`);
                }, 300);
              }
            } else {
              grid.children[first].textContent = '?';
              grid.children[first].style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
              grid.children[first].style.transform = '';
              grid.children[second].textContent = '?';
              grid.children[second].style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
              grid.children[second].style.transform = '';
            }
            
            flipped = [];
            canFlip = true;
          }, 800);
        }
      }

      restartBtn.onclick = createGame;
      createGame();
    },

    cssplay: () => {
      const win = createWindow('cssplay', '💅 CSS Playground', `
        <label class="tw-label">CSS Selector:</label>
        <input type="text" class="tw-input" id="css-selector" placeholder="e.g., .my-class, #my-id, p" value="body">
        
        <label class="tw-label">CSS Code:</label>
        <textarea id="css-code" class="tw-input" rows="10" placeholder="Enter CSS here..." style="font-family:monospace;font-size:13px;">background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 20px;</textarea>
        
        <div style="display:flex;gap:8px;">
          <button class="tw-btn tw-btn-primary" id="css-apply" style="flex:1;">✨ Apply CSS</button>
          <button class="tw-btn tw-btn-danger" id="css-clear" style="flex:1;">🗑️ Clear All</button>
        </div>
        
        <div id="css-status" style="margin-top:15px;padding:12px;background:#f7fafc;border-radius:8px;text-align:center;font-size:13px;color:#4a5568;"></div>
      `, '500px');

      const selector = win.querySelector('#css-selector');
      const code = win.querySelector('#css-code');
      const applyBtn = win.querySelector('#css-apply');
      const clearBtn = win.querySelector('#css-clear');
      const status = win.querySelector('#css-status');

      let styleEl = document.createElement('style');
      styleEl.id = 'aden-css-playground';
      document.head.appendChild(styleEl);

      applyBtn.onclick = () => {
        try {
          const sel = selector.value.trim();
          const css = code.value.trim();
          
          if (!sel) return status.textContent = '⚠️ Enter a selector!';
          
          styleEl.textContent = `${sel} { ${css} }`;
          
          const matched = document.querySelectorAll(sel);
          status.textContent = `✓ Applied to ${matched.length} element(s)`;
        } catch (e) {
          status.textContent = '❌ Invalid CSS: ' + e.message;
        }
      };

      clearBtn.onclick = () => {
        styleEl.textContent = '';
        code.value = '';
        selector.value = 'body';
        status.textContent = '🗑️ All custom CSS cleared';
      };

      status.textContent = 'Ready to apply custom CSS';
    },

    formfill: () => {
      const win = createWindow('formfill', '📋 Form Filler', `
        <button class="tw-btn tw-btn-primary" id="ff-auto">🎲 Auto-Fill Forms</button>
        <button class="tw-btn tw-btn-secondary" id="ff-custom">⚙️ Custom Data</button>
        
        <div id="ff-custom-panel" style="display:none;margin-top:15px;">
          <label class="tw-label">Name:</label>
          <input type="text" class="tw-input" id="ff-name" value="John Doe">
          
          <label class="tw-label">Email:</label>
          <input type="text" class="tw-input" id="ff-email" value="john@example.com">
          
          <label class="tw-label">Phone:</label>
          <input type="text" class="tw-input" id="ff-phone" value="555-0123">
          
          <label class="tw-label">Address:</label>
          <input type="text" class="tw-input" id="ff-address" value="123 Main St">
          
          <button class="tw-btn tw-btn-success" id="ff-apply">✓ Fill Forms</button>
        </div>
        
        <div id="ff-status" style="margin-top:15px;padding:12px;background:#f7fafc;border-radius:8px;text-align:center;font-size:13px;color:#4a5568;"></div>
      `, '450px');

      const autoBtn = win.querySelector('#ff-auto');
      const customBtn = win.querySelector('#ff-custom');
      const customPanel = win.querySelector('#ff-custom-panel');
      const applyBtn = win.querySelector('#ff-apply');
      const status = win.querySelector('#ff-status');

      const nameInput = win.querySelector('#ff-name');
      const emailInput = win.querySelector('#ff-email');
      const phoneInput = win.querySelector('#ff-phone');
      const addressInput = win.querySelector('#ff-address');

      function fillForms(data) {
        const inputs = document.querySelectorAll('input, textarea, select');
        let filled = 0;

        inputs.forEach(input => {
          if (input.closest('.tw, #aden-toolkit')) return;
          
          const name = (input.name || input.id || input.placeholder || '').toLowerCase();
          const type = input.type?.toLowerCase();

          if (name.includes('name') || name.includes('user')) {
            input.value = data.name;
            filled++;
          } else if (name.includes('email') || type === 'email') {
            input.value = data.email;
            filled++;
          } else if (name.includes('phone') || name.includes('tel') || type === 'tel') {
            input.value = data.phone;
            filled++;
          } else if (name.includes('address') || name.includes('street')) {
            input.value = data.address;
            filled++;
          } else if (type === 'text' && !input.value) {
            input.value = 'Test Data';
            filled++;
          }
        });

        status.textContent = `✓ Filled ${filled} field(s)`;
      }

      autoBtn.onclick = () => {
        const randomNames = ['Alice Johnson', 'Bob Smith', 'Carol White', 'David Brown'];
        fillForms({
          name: randomNames[Math.floor(Math.random() * randomNames.length)],
          email: `test${Math.floor(Math.random() * 9999)}@example.com`,
          phone: `555-${Math.floor(Math.random() * 9000) + 1000}`,
          address: `${Math.floor(Math.random() * 999) + 1} Test St`
        });
      };

      customBtn.onclick = () => {
        customPanel.style.display = customPanel.style.display === 'none' ? 'block' : 'none';
      };

      applyBtn.onclick = () => {
        fillForms({
          name: nameInput.value,
          email: emailInput.value,
          phone: phoneInput.value,
          address: addressInput.value
        });
      };

      status.textContent = 'Ready to fill forms on this page';
    },

    converter: () => {
      const conversions = {
        length: {
          meters: 1,
          kilometers: 0.001,
          centimeters: 100,
          millimeters: 1000,
          miles: 0.000621371,
          yards: 1.09361,
          feet: 3.28084,
          inches: 39.3701
        },
        weight: {
          kilograms: 1,
          grams: 1000,
          milligrams: 1000000,
          pounds: 2.20462,
          ounces: 35.274
        },
        temperature: {
          celsius: (v) => v,
          fahrenheit: (v) => (v * 9/5) + 32,
          kelvin: (v) => v + 273.15
        },
        speed: {
          'meters/sec': 1,
          'kilometers/hr': 3.6,
          'miles/hr': 2.23694,
          'feet/sec': 3.28084
        }
      };

      const win = createWindow('converter', '🔄 Unit Converter', `
        <label class="tw-label">Category:</label>
        <select id="conv-category" class="tw-input">
          <option value="length">Length</option>
          <option value="weight">Weight</option>
          <option value="temperature">Temperature</option>
          <option value="speed">Speed</option>
        </select>
        
        <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:end;margin-top:15px;">
          <div>
            <label class="tw-label">From:</label>
            <input type="number" id="conv-from-val" class="tw-input" value="1" style="margin-bottom:8px;">
            <select id="conv-from-unit" class="tw-input"></select>
          </div>
          <div style="font-size:24px;padding-bottom:10px;">→</div>
          <div>
            <label class="tw-label">To:</label>
            <input type="number" id="conv-to-val" class="tw-input" readonly style="margin-bottom:8px;">
            <select id="conv-to-unit" class="tw-input"></select>
          </div>
        </div>
        
        <button class="tw-btn tw-btn-primary" id="conv-swap">🔄 Swap Units</button>
      `, '500px');

      const categorySelect = win.querySelector('#conv-category');
      const fromVal = win.querySelector('#conv-from-val');
      const toVal = win.querySelector('#conv-to-val');
      const fromUnit = win.querySelector('#conv-from-unit');
      const toUnit = win.querySelector('#conv-to-unit');
      const swapBtn = win.querySelector('#conv-swap');

      function populateUnits() {
        const cat = categorySelect.value;
        const units = Object.keys(conversions[cat]);
        
        fromUnit.innerHTML = units.map(u => `<option value="${u}">${u}</option>`).join('');
        toUnit.innerHTML = units.map(u => `<option value="${u}">${u}</option>`).join('');
        toUnit.selectedIndex = 1;
        convert();
      }

      function convert() {
        const cat = categorySelect.value;
        const val = parseFloat(fromVal.value) || 0;
        const from = fromUnit.value;
        const to = toUnit.value;

        if (cat === 'temperature') {
          let celsius = val;
          if (from === 'fahrenheit') celsius = (val - 32) * 5/9;
          if (from === 'kelvin') celsius = val - 273.15;
          
          toVal.value = conversions[cat][to](celsius).toFixed(2);
        } else {
          const baseVal = val / conversions[cat][from];
          toVal.value = (baseVal * conversions[cat][to]).toFixed(4);
        }
      }

      categorySelect.onchange = populateUnits;
      fromVal.oninput = convert;
      fromUnit.onchange = convert;
      toUnit.onchange = convert;

      swapBtn.onclick = () => {
        const tempUnit = fromUnit.value;
        fromUnit.value = toUnit.value;
        toUnit.value = tempUnit;
        fromVal.value = toVal.value;
        convert();
      };

      populateUnits();
    },

    lorem: () => {
      const win = createWindow('lorem', '📄 Lorem Ipsum Generator', `
        <label class="tw-label">Type:</label>
        <select id="lorem-type" class="tw-input">
          <option value="paragraphs">Paragraphs</option>
          <option value="sentences">Sentences</option>
          <option value="words">Words</option>
        </select>
        
        <label class="tw-label">Amount:</label>
        <input type="number" id="lorem-amount" class="tw-input" value="3" min="1" max="100">
        
        <button class="tw-btn tw-btn-primary" id="lorem-generate">✨ Generate</button>
        
        <label class="tw-label">Generated Text:</label>
        <textarea id="lorem-output" class="tw-input" rows="10" readonly style="font-size:13px;"></textarea>
        
        <button class="tw-btn tw-btn-success" id="lorem-copy">📋 Copy to Clipboard</button>
      `, '550px');

      const typeSelect = win.querySelector('#lorem-type');
      const amountInput = win.querySelector('#lorem-amount');
      const generateBtn = win.querySelector('#lorem-generate');
      const output = win.querySelector('#lorem-output');
      const copyBtn = win.querySelector('#lorem-copy');

      const loremWords = ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit', 'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore', 'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud', 'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo', 'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate', 'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint', 'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia', 'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum'];

      function generateWords(count) {
        const words = [];
        for (let i = 0; i < count; i++) {
          words.push(loremWords[Math.floor(Math.random() * loremWords.length)]);
        }
        return words;
      }

      function generateSentence() {
        const words = generateWords(Math.floor(Math.random() * 10) + 5);
        words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
        return words.join(' ') + '.';
      }

      function generateParagraph() {
        const sentences = [];
        const sentenceCount = Math.floor(Math.random() * 4) + 3;
        for (let i = 0; i < sentenceCount; i++) {
          sentences.push(generateSentence());
        }
        return sentences.join(' ');
      }

      generateBtn.onclick = () => {
        const type = typeSelect.value;
        const amount = parseInt(amountInput.value) || 1;
        let result = '';

        if (type === 'paragraphs') {
          const paragraphs = [];
          for (let i = 0; i < amount; i++) {
            paragraphs.push(generateParagraph());
          }
          result = paragraphs.join('\n\n');
        } else if (type === 'sentences') {
          const sentences = [];
          for (let i = 0; i < amount; i++) {
            sentences.push(generateSentence());
          }
          result = sentences.join(' ');
        } else if (type === 'words') {
          result = generateWords(amount).join(' ');
        }

        output.value = result;
      };

      copyBtn.onclick = () => {
        output.select();
        navigator.clipboard.writeText(output.value);
        copyBtn.textContent = '✓ Copied!';
        setTimeout(() => copyBtn.textContent = '📋 Copy to Clipboard', 1500);
      };

      generateBtn.click();
    },

    performance: () => {
      const win = createWindow('performance', '📊 Performance Monitor', `
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-bottom:20px;">
          <div style="background:#f7fafc;padding:15px;border-radius:10px;text-align:center;">
            <div style="font-size:32px;font-weight:900;color:#667eea;" id="perf-fps">0</div>
            <div style="font-size:12px;color:#718096;margin-top:5px;">FPS</div>
          </div>
          <div style="background:#f7fafc;padding:15px;border-radius:10px;text-align:center;">
            <div style="font-size:32px;font-weight:900;color:#48bb78;" id="perf-memory">0</div>
            <div style="font-size:12px;color:#718096;margin-top:5px;">Memory (MB)</div>
          </div>
        </div>
        
        <div style="background:#f7fafc;padding:15px;border-radius:10px;margin-bottom:15px;">
          <div style="font-weight:700;margin-bottom:10px;">Page Load Metrics:</div>
          <div style="font-size:13px;line-height:1.8;" id="perf-metrics"></div>
        </div>
        
        <div style="background:#f7fafc;padding:15px;border-radius:10px;">
          <div style="font-weight:700;margin-bottom:10px;">Resources:</div>
          <div style="font-size:13px;line-height:1.8;" id="perf-resources"></div>
        </div>
      `, '500px');

      const fpsEl = win.querySelector('#perf-fps');
      const memoryEl = win.querySelector('#perf-memory');
      const metricsEl = win.querySelector('#perf-metrics');
      const resourcesEl = win.querySelector('#perf-resources');

      // FPS Counter
      let fps = 0;
      let lastTime = performance.now();
      let frames = 0;

      function updateFPS() {
        frames++;
        const now = performance.now();
        if (now >= lastTime + 1000) {
          fps = Math.round((frames * 1000) / (now - lastTime));
          fpsEl.textContent = fps;
          frames = 0;
          lastTime = now;
        }
        if (win.parentNode) requestAnimationFrame(updateFPS);
      }
      requestAnimationFrame(updateFPS);

      // Memory Usage
      function updateMemory() {
        if (performance.memory) {
          const used = (performance.memory.usedJSHeapSize / 1048576).toFixed(2);
          memoryEl.textContent = used;
        } else {
          memoryEl.textContent = 'N/A';
        }
      }
      setInterval(updateMemory, 1000);
      updateMemory();

      // Page Load Metrics
      const perfData = performance.timing;
      const loadTime = perfData.loadEventEnd - perfData.navigationStart;
      const domReady = perfData.domContentLoadedEventEnd - perfData.navigationStart;
      const connectTime = perfData.responseEnd - perfData.requestStart;

      metricsEl.innerHTML = `
        <div>⚡ Page Load: <strong>${loadTime}ms</strong></div>
        <div>🔷 DOM Ready: <strong>${domReady}ms</strong></div>
        <div>🌐 Server Response: <strong>${connectTime}ms</strong></div>
      `;

      // Resources
      const resources = performance.getEntriesByType('resource');
      const scripts = resources.filter(r => r.initiatorType === 'script').length;
      const styles = resources.filter(r => r.initiatorType === 'link').length;
      const images = resources.filter(r => r.initiatorType === 'img').length;

      resourcesEl.innerHTML = `
        <div>📜 Scripts: <strong>${scripts}</strong></div>
        <div>🎨 Stylesheets: <strong>${styles}</strong></div>
        <div>🖼️ Images: <strong>${images}</strong></div>
        <div>📦 Total Resources: <strong>${resources.length}</strong></div>
      `;
    },

    screenshot: () => {
      const win = createWindow('screenshot', '📸 Screenshot Tool', `
        <div style="text-align:center;">
          <div style="background:#f7fafc;padding:20px;border-radius:10px;margin-bottom:15px;">
            <div style="font-size:48px;margin-bottom:10px;">📸</div>
            <div style="font-size:14px;color:#718096;">Capture any part of the page</div>
          </div>
          
          <button class="tw-btn tw-btn-primary" id="ss-select">📐 Select Area</button>
          <button class="tw-btn tw-btn-success" id="ss-full">🖥️ Full Page</button>
          <button class="tw-btn tw-btn-secondary" id="ss-visible">👁️ Visible Area</button>
          
          <div id="ss-preview" style="margin-top:15px;display:none;">
            <label class="tw-label">Preview:</label>
            <img id="ss-img" style="max-width:100%;border-radius:8px;border:2px solid #e2e8f0;">
            <button class="tw-btn tw-btn-success" id="ss-download" style="margin-top:10px;">💾 Download</button>
          </div>
        </div>
      `, '450px');

      const selectBtn = win.querySelector('#ss-select');
      const fullBtn = win.querySelector('#ss-full');
      const visibleBtn = win.querySelector('#ss-visible');
      const preview = win.querySelector('#ss-preview');
      const img = win.querySelector('#ss-img');
      const downloadBtn = win.querySelector('#ss-download');

      let screenshotData = null;

      async function takeScreenshot(element) {
        try {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          const rect = element.getBoundingClientRect();
          
          canvas.width = rect.width;
          canvas.height = rect.height;

          // Simple background color capture
          const bgColor = window.getComputedStyle(element).backgroundColor;
          ctx.fillStyle = bgColor;
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          // Add text indicating screenshot
          ctx.fillStyle = '#667eea';
          ctx.font = '20px Arial';
          ctx.textAlign = 'center';
          ctx.fillText('Screenshot captured!', canvas.width/2, canvas.height/2);
          ctx.fillText('(HTML2Canvas not available)', canvas.width/2, canvas.height/2 + 30);

          screenshotData = canvas.toDataURL('image/png');
          img.src = screenshotData;
          preview.style.display = 'block';
        } catch (e) {
          alert('Screenshot failed: ' + e.message);
        }
      }

      selectBtn.onclick = () => {
        alert('Click on any element to screenshot it!');
        const handler = (e) => {
          if (e.target.closest('.tw')) return;
          e.preventDefault();
          e.stopPropagation();
          takeScreenshot(e.target);
          document.removeEventListener('click', handler, true);
        };
        document.addEventListener('click', handler, true);
      };

      fullBtn.onclick = () => takeScreenshot(document.documentElement);
      visibleBtn.onclick = () => takeScreenshot(document.body);

      downloadBtn.onclick = () => {
        const a = document.createElement('a');
        a.href = screenshotData;
        a.download = `screenshot-${Date.now()}.png`;
        a.click();
      };
    },

    linkchecker: () => {
      const win = createWindow('linkchecker', '🔗 Link Checker', `
        <button class="tw-btn tw-btn-primary" id="lc-scan">🔍 Scan Page Links</button>
        
        <div id="lc-results" style="margin-top:15px;display:none;">
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:15px;">
            <div style="background:#f7fafc;padding:12px;border-radius:8px;text-align:center;">
              <div style="font-size:24px;font-weight:900;color:#667eea;" id="lc-total">0</div>
              <div style="font-size:11px;color:#718096;">Total Links</div>
            </div>
            <div style="background:#f7fafc;padding:12px;border-radius:8px;text-align:center;">
              <div style="font-size:24px;font-weight:900;color:#48bb78;" id="lc-internal">0</div>
              <div style="font-size:11px;color:#718096;">Internal</div>
            </div>
            <div style="background:#f7fafc;padding:12px;border-radius:8px;text-align:center;">
              <div style="font-size:24px;font-weight:900;color:#f6ad55;" id="lc-external">0</div>
              <div style="font-size:11px;color:#718096;">External</div>
            </div>
          </div>
          
          <label class="tw-label">All Links:</label>
          <div id="lc-list" style="max-height:300px;overflow-y:auto;background:#f7fafc;border-radius:8px;padding:10px;"></div>
        </div>
      `, '550px');

      const scanBtn = win.querySelector('#lc-scan');
      const results = win.querySelector('#lc-results');
      const totalEl = win.querySelector('#lc-total');
      const internalEl = win.querySelector('#lc-internal');
      const externalEl = win.querySelector('#lc-external');
      const listEl = win.querySelector('#lc-list');

      scanBtn.onclick = () => {
        const links = Array.from(document.querySelectorAll('a[href]'));
        const currentDomain = window.location.hostname;
        
        let internal = 0;
        let external = 0;

        const linkHTML = links.map((link, i) => {
          const href = link.href;
          const isInternal = href.includes(currentDomain) || href.startsWith('/') || href.startsWith('#');
          
          if (isInternal) internal++;
          else external++;

          const icon = isInternal ? '🏠' : '🌐';
          const color = isInternal ? '#48bb78' : '#f6ad55';

          return `
            <div style="padding:8px;margin:5px 0;background:white;border-radius:6px;border-left:3px solid ${color};">
              <div style="font-size:12px;font-weight:700;color:${color};">${icon} ${isInternal ? 'Internal' : 'External'}</div>
              <div style="font-size:11px;color:#4a5568;margin-top:3px;word-break:break-all;">${href}</div>
              ${link.textContent.trim() ? `<div style="font-size:11px;color:#718096;margin-top:2px;">"${link.textContent.trim().substring(0, 50)}..."</div>` : ''}
            </div>
          `;
        }).join('');

        totalEl.textContent = links.length;
        internalEl.textContent = internal;
        externalEl.textContent = external;
        listEl.innerHTML = linkHTML || '<div style="text-align:center;color:#718096;padding:20px;">No links found</div>';
        
        results.style.display = 'block';
        scanBtn.textContent = '🔄 Re-scan Links';
      };
    },
  };

  function launchTool(id) {
    if (TOOLS[id]) {
      TOOLS[id]();
    } else {
      alert('🚧 Tool not implemented yet!');
    }
  }(function() {
  // Remove existing
  const existing = document.getElementById('aden-toolkit');
  if (existing) existing.remove();

  const container = document.createElement('div');
  container.id = 'aden-toolkit';
  document.body.appendChild(container);

  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    #aden-toolkit *, #aden-toolkit *::before, #aden-toolkit *::after {box-sizing: border-box;}
    .tk-launcher {position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 850px; max-width: 95vw; max-height: 90vh; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-radius: 24px; padding: 30px; box-shadow: 0 25px 80px rgba(0,0,0,0.4); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: white; z-index: 999999; overflow-y: auto;}
    .tk-header {text-align: center; margin-bottom: 25px;}
    .tk-title {font-size: 42px; font-weight: 900; margin-bottom: 8px; background: linear-gradient(45deg, #fff, #a8dadc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-shadow: 0 2px 10px rgba(0,0,0,0.2);}
    .tk-subtitle {font-size: 15px; opacity: 0.85; font-weight: 500;}
    .tk-close {position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2); border: none; color: white; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; font-size: 24px; transition: all 0.3s; font-weight: 700;}
    .tk-close:hover {background: rgba(255,255,255,0.3); transform: rotate(90deg) scale(1.1);}
    .tk-search {width: 100%; padding: 15px 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 50px; background: rgba(255,255,255,0.15); color: white; font-size: 15px; margin-bottom: 25px; backdrop-filter: blur(10px);}
    .tk-search::placeholder {color: rgba(255,255,255,0.6);}
    .tk-search:focus {outline: none; border-color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.2);}
    .tk-grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 15px; margin-bottom: 20px;}
    .tk-tool {background: rgba(255,255,255,0.12); backdrop-filter: blur(10px); border-radius: 18px; padding: 24px 20px; cursor: pointer; transition: all 0.3s; border: 2px solid transparent; text-align: center;}
    .tk-tool:hover {transform: translateY(-8px); background: rgba(255,255,255,0.22); border-color: rgba(255,255,255,0.4); box-shadow: 0 15px 40px rgba(0,0,0,0.3);}
    .tk-tool-icon {font-size: 40px; margin-bottom: 12px; display: block; transform: scale(1); transition: transform 0.3s;}
    .tk-tool:hover .tk-tool-icon {transform: scale(1.15);}
    .tk-tool-name {font-size: 15px; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.3px;}
    .tk-tool-desc {font-size: 12px; opacity: 0.8; line-height: 1.4;}
    .tk-tool-tag {display: inline-block; font-size: 10px; background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 10px; margin-top: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
    .tk-footer {text-align: center; font-size: 13px; opacity: 0.75; margin-top: 25px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); font-weight: 500;}
    
    .tw {position: fixed; background: white; border-radius: 18px; box-shadow: 0 20px 60px rgba(0,0,0,0.35); color: #333; z-index: 999998; overflow: hidden;}
    .tw-header {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 22px; display: flex; justify-content: space-between; align-items: center; cursor: move; user-select: none;}
    .tw-title {font-weight: 700; font-size: 17px; display: flex; align-items: center; gap: 8px;}
    .tw-close {background: rgba(255,255,255,0.25); border: none; color: white; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; font-size: 20px; font-weight: 700; transition: all 0.2s;}
    .tw-close:hover {background: rgba(255,255,255,0.4); transform: scale(1.1);}
    .tw-body {padding: 22px; max-height: 70vh; overflow-y: auto;}
    .tw-btn {padding: 12px 18px; border: none; border-radius: 10px; cursor: pointer; font-weight: 700; font-size: 14px; transition: all 0.2s; width: 100%; margin: 6px 0;}
    .tw-btn:hover {transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15);}
    .tw-btn-primary {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;}
    .tw-btn-success {background: #48bb78; color: white;}
    .tw-btn-danger {background: #f56565; color: white;}
    .tw-btn-secondary {background: #e2e8f0; color: #2d3748;}
    .tw-input {width: 100%; padding: 12px 14px; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 14px; margin: 6px 0; transition: all 0.2s;}
    .tw-input:focus {outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1);}
    .tw-label {font-weight: 700; font-size: 13px; color: #4a5568; margin: 12px 0 6px 0; display: block;}
  `;
  document.head.appendChild(style);

  const tools = [
    {id: 'autoclicker', name: 'Auto Clicker', icon: '🖱️', desc: 'Click anywhere automatically', tag: 'productivity'},
    {id: 'colorpicker', name: 'Color Picker', icon: '🎨', desc: 'Grab colors from page', tag: 'design'},
    {id: 'inspector', name: 'Page Inspector', icon: '🔍', desc: 'Inspect any element', tag: 'dev'},
    {id: 'darkmode', name: 'Dark Mode', icon: '🌙', desc: 'Toggle dark theme', tag: 'utility'},
    {id: 'videospeed', name: 'Video Speed', icon: '⏩', desc: 'Control playback speed', tag: 'media'},
    {id: 'textreplace', name: 'Text Replacer', icon: '✏️', desc: 'Find & replace text', tag: 'utility'},
    {id: 'calculator', name: 'Calculator', icon: '🔢', desc: 'Scientific calculator', tag: 'utility'},
    {id: 'timer', name: 'Pomodoro Timer', icon: '⏱️', desc: '25 min focus sessions', tag: 'productivity'},
    {id: 'notes', name: 'Quick Notes', icon: '📝', desc: 'Sticky notes', tag: 'productivity'},
    {id: 'snake', name: 'Snake Game', icon: '🐍', desc: 'Classic arcade fun', tag: 'game'},
    {id: 'typing', name: 'Typing Test', icon: '⌨️', desc: 'Test your WPM', tag: 'game'},
    {id: 'memory', name: 'Memory Cards', icon: '🎴', desc: 'Match the pairs', tag: 'game'},
    {id: 'cssplay', name: 'CSS Playground', icon: '💅', desc: 'Live CSS editor', tag: 'dev'},
    {id: 'formfill', name: 'Form Filler', icon: '📋', desc: 'Auto-fill test data', tag: 'dev'},
    {id: 'converter', name: 'Unit Converter', icon: '🔄', desc: 'Convert anything', tag: 'utility'},
    {id: 'lorem', name: 'Lorem Ipsum', icon: '📄', desc: 'Generate placeholder', tag: 'dev'},
    {id: 'screenshot', name: 'Screenshot', icon: '📸', desc: 'Capture page areas', tag: 'utility'},
    {id: 'performance', name: 'Performance', icon: '📊', desc: 'Monitor FPS & memory', tag: 'dev'},
  ];

  function showLauncher() {
    const launcher = document.createElement('div');
    launcher.className = 'tk-launcher';
    launcher.innerHTML = `
      <button class="tk-close">×</button>
      <div class="tk-header">
        <div class="tk-title">🚀 Console Toolkit</div>
        <div class="tk-subtitle">Ultimate browser enhancement suite · ${tools.length} tools loaded</div>
      </div>
      <input type="text" class="tk-search" placeholder="🔎 Search tools..." id="tk-search">
      <div class="tk-grid" id="tk-grid"></div>
      <div class="tk-footer">Created by Aden · Press Ctrl+Shift+K to reopen</div>
    `;
    container.appendChild(launcher);

    launcher.querySelector('.tk-close').onclick = () => launcher.remove();

    const grid = launcher.querySelector('#tk-grid');
    const search = launcher.querySelector('#tk-search');

    function render(filter = '') {
      const filtered = tools.filter(t => 
        t.name.toLowerCase().includes(filter.toLowerCase()) ||
        t.desc.toLowerCase().includes(filter.toLowerCase()) ||
        t.tag.toLowerCase().includes(filter.toLowerCase())
      );
      
      grid.innerHTML = filtered.map(t => `
        <div class="tk-tool" data-id="${t.id}">
          <span class="tk-tool-icon">${t.icon}</span>
          <div class="tk-tool-name">${t.name}</div>
          <div class="tk-tool-desc">${t.desc}</div>
          <span class="tk-tool-tag">${t.tag}</span>
        </div>
      `).join('');
    }

    render();
    search.oninput = (e) => render(e.target.value);

    grid.onclick = (e) => {
      const tool = e.target.closest('.tk-tool');
      if (tool) {
        const id = tool.dataset.id;
        launcher.remove();
        launchTool(id);
      }
    };
  }

  function createWindow(id, title, content, width = '420px') {
    const existing = container.querySelector(`#tw-${id}`);
    if (existing) {
      existing.style.display = 'block';
      return existing;
    }

    const win = document.createElement('div');
    win.id = `tw-${id}`;
    win.className = 'tw';
    win.style.width = width;
    win.style.left = `${100 + Math.random() * 200}px`;
    win.style.top = `${80 + Math.random() * 100}px`;
    win.innerHTML = `
      <div class="tw-header">
        <div class="tw-title">${title}</div>
        <button class="tw-close">×</button>
      </div>
      <div class="tw-body">${content}</div>
    `;
    container.appendChild(win);

    win.querySelector('.tw-close').onclick = () => win.remove();

    // Make draggable
    const header = win.querySelector('.tw-header');
    let pos1=0, pos2=0, pos3=0, pos4=0;
    header.onmousedown = (e) => {
      e.preventDefault();
      pos3 = e.clientX;
      pos4 = e.clientY;
      document.onmouseup = () => {document.onmouseup = null; document.onmousemove = null;};
      document.onmousemove = (e) => {
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        win.style.top = (win.offsetTop - pos2) + 'px';
        win.style.left = (win.offsetLeft - pos1) + 'px';
      };
    };

    return win;
  }

  // === TOOL IMPLEMENTATIONS ===

  const TOOLS = {
    calculator: () => {
      const win = createWindow('calc', '🔢 Calculator', `
        <input type="text" id="calc-display" class="tw-input" value="0" readonly style="font-size:24px;text-align:right;font-family:monospace;margin-bottom:15px;">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">
          ${['7','8','9','/','4','5','6','*','1','2','3','-','0','.','=','+'].map(b => 
            `<button class="tw-btn tw-btn-secondary calc-btn" style="padding:18px;font-size:18px;font-weight:700;">${b}</button>`
          ).join('')}
        </div>
        <button class="tw-btn tw-btn-danger" id="calc-clear" style="margin-top:8px;">Clear</button>
      `, '340px');

      const display = win.querySelector('#calc-display');
      let current = '0', operator = null, previous = null;

      win.querySelectorAll('.calc-btn').forEach(btn => {
        btn.onclick = () => {
          const val = btn.textContent;
          if ('0123456789.'.includes(val)) {
            current = current === '0' ? val : current + val;
            display.value = current;
          } else if ('+-*/'.includes(val)) {
            previous = parseFloat(current);
            operator = val;
            current = '0';
          } else if (val === '=') {
            if (operator && previous !== null) {
              const curr = parseFloat(current);
              let result;
              if (operator === '+') result = previous + curr;
              else if (operator === '-') result = previous - curr;
              else if (operator === '*') result = previous * curr;
              else if (operator === '/') result = previous / curr;
              display.value = result;
              current = String(result);
              operator = null;
              previous = null;
            }
          }
        };
      });

      win.querySelector('#calc-clear').onclick = () => {
        current = '0';
        operator = null;
        previous = null;
        display.value = '0';
      };
    },

    timer: () => {
      const win = createWindow('timer', '⏱️ Timer & Clock', `
        <div style="text-align:center;">
          <div style="display:flex;gap:8px;margin-bottom:20px;">
            <button class="tw-btn tw-btn-secondary mode-btn" data-mode="timer" style="flex:1;background:#667eea;color:white;">⏱️ Timer</button>
            <button class="tw-btn tw-btn-secondary mode-btn" data-mode="stopwatch" style="flex:1;">⏲️ Stopwatch</button>
            <button class="tw-btn tw-btn-secondary mode-btn" data-mode="clock" style="flex:1;">🕐 Clock</button>
          </div>
          
          <div id="timer-mode">
            <div style="font-size:72px;font-weight:900;font-family:monospace;color:#667eea;margin:20px 0;" id="timer-display">00:00</div>
            <div style="display:flex;gap:10px;margin-bottom:15px;">
              <div style="flex:1;">
                <label class="tw-label" style="margin:0 0 5px 0;font-size:11px;">Hours</label>
                <input type="number" class="tw-input" id="timer-hours" value="0" min="0" style="text-align:center;padding:10px;">
              </div>
              <div style="flex:1;">
                <label class="tw-label" style="margin:0 0 5px 0;font-size:11px;">Minutes</label>
                <input type="number" class="tw-input" id="timer-minutes" value="5" min="0" max="59" style="text-align:center;padding:10px;">
              </div>
              <div style="flex:1;">
                <label class="tw-label" style="margin:0 0 5px 0;font-size:11px;">Seconds</label>
                <input type="number" class="tw-input" id="timer-seconds" value="0" min="0" max="59" style="text-align:center;padding:10px;">
              </div>
            </div>
            <div style="display:flex;gap:10px;">
              <button class="tw-btn tw-btn-success" id="timer-start" style="flex:1;">▶ Start</button>
              <button class="tw-btn tw-btn-danger" id="timer-reset" style="flex:1;">↻ Reset</button>
            </div>
            <div style="margin-top:15px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
              <button class="tw-btn tw-btn-secondary quick-btn" data-time="60">1 min</button>
              <button class="tw-btn tw-btn-secondary quick-btn" data-time="300">5 min</button>
              <button class="tw-btn tw-btn-secondary quick-btn" data-time="600">10 min</button>
              <button class="tw-btn tw-btn-secondary quick-btn" data-time="900">15 min</button>
              <button class="tw-btn tw-btn-secondary quick-btn" data-time="1500">25 min</button>
              <button class="tw-btn tw-btn-secondary quick-btn" data-time="3600">1 hour</button>
            </div>
          </div>
          
          <div id="stopwatch-mode" style="display:none;">
            <div style="font-size:72px;font-weight:900;font-family:monospace;color:#48bb78;margin:20px 0;" id="stopwatch-display">00:00:00</div>
            <div style="display:flex;gap:10px;">
              <button class="tw-btn tw-btn-success" id="stopwatch-start" style="flex:1;">▶ Start</button>
              <button class="tw-btn tw-btn-danger" id="stopwatch-reset" style="flex:1;">↻ Reset</button>
            </div>
            <div id="stopwatch-laps" style="margin-top:15px;max-height:150px;overflow-y:auto;"></div>
          </div>
          
          <div id="clock-mode" style="display:none;">
            <div style="font-size:72px;font-weight:900;font-family:monospace;color:#f6ad55;margin:20px 0;" id="clock-display">00:00:00</div>
            <div style="font-size:18px;color:#718096;margin-top:10px;" id="clock-date">Loading...</div>
            <div style="display:flex;gap:10px;margin-top:20px;">
              <button class="tw-btn tw-btn-secondary" id="clock-12h" style="flex:1;">12 Hour</button>
              <button class="tw-btn tw-btn-secondary" id="clock-24h" style="flex:1;background:#667eea;color:white;">24 Hour</button>
            </div>
          </div>
        </div>
      `, '450px');

      const modeBtns = win.querySelectorAll('.mode-btn');
      const timerMode = win.querySelector('#timer-mode');
      const stopwatchMode = win.querySelector('#stopwatch-mode');
      const clockMode = win.querySelector('#clock-mode');
      
      let currentMode = 'timer';
      let interval = null;

      // Mode switching
      modeBtns.forEach(btn => {
        btn.onclick = () => {
          modeBtns.forEach(b => {
            b.style.background = '';
            b.style.color = '';
          });
          btn.style.background = '#667eea';
          btn.style.color = 'white';
          
          timerMode.style.display = 'none';
          stopwatchMode.style.display = 'none';
          clockMode.style.display = 'none';
          
          currentMode = btn.dataset.mode;
          if (currentMode === 'timer') timerMode.style.display = 'block';
          else if (currentMode === 'stopwatch') stopwatchMode.style.display = 'block';
          else if (currentMode === 'clock') {
            clockMode.style.display = 'block';
            startClock();
          }
          
          if (interval) clearInterval(interval);
        };
      });

      // === TIMER MODE ===
      const timerDisplay = win.querySelector('#timer-display');
      const timerStart = win.querySelector('#timer-start');
      const timerReset = win.querySelector('#timer-reset');
      const hoursInput = win.querySelector('#timer-hours');
      const minutesInput = win.querySelector('#timer-minutes');
      const secondsInput = win.querySelector('#timer-seconds');
      
      let timerSeconds = 300;
      let timerRunning = false;

      function updateTimerDisplay() {
        const h = Math.floor(timerSeconds / 3600);
        const m = Math.floor((timerSeconds % 3600) / 60);
        const s = timerSeconds % 60;
        
        if (h > 0) {
          timerDisplay.textContent = `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        } else {
          timerDisplay.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
      }

      function setTimerFromInputs() {
        const h = parseInt(hoursInput.value) || 0;
        const m = parseInt(minutesInput.value) || 0;
        const s = parseInt(secondsInput.value) || 0;
        timerSeconds = h * 3600 + m * 60 + s;
        updateTimerDisplay();
      }

      [hoursInput, minutesInput, secondsInput].forEach(input => {
        input.oninput = setTimerFromInputs;
      });

      timerStart.onclick = () => {
        if (timerRunning) {
          clearInterval(interval);
          timerStart.textContent = '▶ Start';
          timerRunning = false;
        } else {
          if (timerSeconds === 0) setTimerFromInputs();
          if (timerSeconds === 0) return;
          
          interval = setInterval(() => {
            if (timerSeconds > 0) {
              timerSeconds--;
              updateTimerDisplay();
            } else {
              clearInterval(interval);
              timerStart.textContent = '▶ Start';
              timerRunning = false;
              alert('⏰ Timer complete!');
              new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBjGJ0fPTgjMGHWm98OOpWRIIR5vd8sdyJQUzhdT12I4+CRZiturqpFsVCU2d4vK8aB8GM4nU9duIOQcZaLzy6KNaFApIodvyvmsgBi+F0/XajT0KFmG26+mjWBUITJ3h8sFsIQYzie/z24s8CBdou/DlpFsUCEmh2/K+ayEGMIjU9t2KOggcabvy5qNZEwhKnuD0wGofBzGJ1PbciToIGmm88OiiWxQJSZ7f9L9pHwczidP23Yk6CBtpvO/nolsUCUme3/TAaB8HM4nU9t2JOQgbaLzw6KJbFAlJnt/0wGkfBzOJ0/bdiToHG2m88OiiWhQJSZ7f9MBpHwczidP23Io5CBtpvPDnolsUCUqe3vTAaR8GM4jU9tyKOQgcaLvv56JbFApKnt/1v2kfBzOJ1Pbci== ' ).play().catch(() => {});
            }
          }, 1000);
          timerStart.textContent = '⏸ Pause';
          timerRunning = true;
        }
      };

      timerReset.onclick = () => {
        clearInterval(interval);
        setTimerFromInputs();
        timerStart.textContent = '▶ Start';
        timerRunning = false;
      };

      win.querySelectorAll('.quick-btn').forEach(btn => {
        btn.onclick = () => {
          clearInterval(interval);
          timerSeconds = parseInt(btn.dataset.time);
          const h = Math.floor(timerSeconds / 3600);
          const m = Math.floor((timerSeconds % 3600) / 60);
          const s = timerSeconds % 60;
          hoursInput.value = h;
          minutesInput.value = m;
          secondsInput.value = s;
          updateTimerDisplay();
          timerStart.textContent = '▶ Start';
          timerRunning = false;
        };
      });

      updateTimerDisplay();

      // === STOPWATCH MODE ===
      const stopwatchDisplay = win.querySelector('#stopwatch-display');
      const stopwatchStart = win.querySelector('#stopwatch-start');
      const stopwatchReset = win.querySelector('#stopwatch-reset');
      const lapsDiv = win.querySelector('#stopwatch-laps');
      
      let stopwatchMs = 0;
      let stopwatchRunning = false;
      let lapCount = 0;

      function updateStopwatchDisplay() {
        const totalSeconds = Math.floor(stopwatchMs / 1000);
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;
        const ms = Math.floor((stopwatchMs % 1000) / 10);
        stopwatchDisplay.textContent = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
      }

      stopwatchStart.onclick = () => {
        if (stopwatchRunning) {
          clearInterval(interval);
          stopwatchStart.textContent = '▶ Start';
          stopwatchRunning = false;
        } else {
          const startTime = Date.now() - stopwatchMs;
          interval = setInterval(() => {
            stopwatchMs = Date.now() - startTime;
            updateStopwatchDisplay();
          }, 10);
          stopwatchStart.textContent = '⏸ Pause';
          stopwatchRunning = true;
        }
      };

      stopwatchReset.onclick = () => {
        if (stopwatchRunning) {
          // Lap
          lapCount++;
          const lapTime = stopwatchDisplay.textContent;
          const lap = document.createElement('div');
          lap.style.cssText = 'padding:8px;background:#f7fafc;border-radius:6px;margin:5px 0;display:flex;justify-content:space-between;color:#2d3748;';
          lap.innerHTML = `<span style="font-weight:700;">Lap ${lapCount}</span><span style="font-family:monospace;">${lapTime}</span>`;
          lapsDiv.insertBefore(lap, lapsDiv.firstChild);
        } else {
          // Reset
          clearInterval(interval);
          stopwatchMs = 0;
          lapCount = 0;
          lapsDiv.innerHTML = '';
          updateStopwatchDisplay();
          stopwatchStart.textContent = '▶ Start';
        }
      };

      updateStopwatchDisplay();

      // === CLOCK MODE ===
      const clockDisplay = win.querySelector('#clock-display');
      const clockDate = win.querySelector('#clock-date');
      const clock12h = win.querySelector('#clock-12h');
      const clock24h = win.querySelector('#clock-24h');
      
      let is24Hour = true;
      let clockInterval = null;

      function updateClock() {
        const now = new Date();
        let h = now.getHours();
        const m = now.getMinutes();
        const s = now.getSeconds();
        
        let displayHour = h;
        let ampm = '';
        
        if (!is24Hour) {
          ampm = h >= 12 ? ' PM' : ' AM';
          displayHour = h % 12 || 12;
        }
        
        clockDisplay.textContent = `${displayHour.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}${ampm}`;
        
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        clockDate.textContent = `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}`;
      }

      function startClock() {
        if (clockInterval) clearInterval(clockInterval);
        updateClock();
        clockInterval = setInterval(updateClock, 1000);
      }

      clock12h.onclick = () => {
        is24Hour = false;
        clock12h.style.background = '#667eea';
        clock12h.style.color = 'white';
        clock24h.style.background = '';
        clock24h.style.color = '';
        updateClock();
      };

      clock24h.onclick = () => {
        is24Hour = true;
        clock24h.style.background = '#667eea';
        clock24h.style.color = 'white';
        clock12h.style.background = '';
        clock12h.style.color = '';
        updateClock();
      };
    },

    notes: () => {
      const win = createWindow('notes', '📝 Quick Notes', `
        <textarea id="notes-text" class="tw-input" rows="12" placeholder="Type your notes here..." style="resize:vertical;font-family:inherit;"></textarea>
        <div style="display:flex;gap:8px;margin-top:10px;">
          <button class="tw-btn tw-btn-primary" id="notes-save" style="flex:1;">💾 Save</button>
          <button class="tw-btn tw-btn-secondary" id="notes-clear" style="flex:1;">🗑️ Clear</button>
        </div>
        <div id="notes-status" style="text-align:center;margin-top:10px;font-size:12px;color:#718096;"></div>
      `, '450px');

      const textarea = win.querySelector('#notes-text');
      const saveBtn = win.querySelector('#notes-save');
      const clearBtn = win.querySelector('#notes-clear');
      const status = win.querySelector('#notes-status');

      const saved = localStorage.getItem('aden-notes');
      if (saved) textarea.value = saved;

      saveBtn.onclick = () => {
        localStorage.setItem('aden-notes', textarea.value);
        status.textContent = '✓ Saved!';
        setTimeout(() => status.textContent = '', 2000);
      };

      clearBtn.onclick = () => {
        if (confirm('Clear all notes?')) {
          textarea.value = '';
          localStorage.removeItem('aden-notes');
        }
      };
    },

    colorpicker: () => {
      const win = createWindow('color', '🎨 Color Picker', `
        <div style="width:100%;height:100px;border-radius:12px;margin-bottom:15px;border:3px solid #e2e8f0;" id="color-preview"></div>
        <input type="text" class="tw-input" id="color-value" readonly style="text-align:center;font-size:20px;font-weight:700;font-family:monospace;">
        <button class="tw-btn tw-btn-primary" id="color-pick">🎨 Pick Color from Page</button>
        <button class="tw-btn tw-btn-success" id="color-copy">📋 Copy to Clipboard</button>
        <label class="tw-label">Recent Colors:</label>
        <div id="color-palette" style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:10px;"></div>
      `, '400px');

      const preview = win.querySelector('#color-preview');
      const valueInput = win.querySelector('#color-value');
      const pickBtn = win.querySelector('#color-pick');
      const copyBtn = win.querySelector('#color-copy');
      const palette = win.querySelector('#color-palette');

      let currentColor = '#667eea';
      let colors = JSON.parse(localStorage.getItem('aden-colors') || '[]');

      function setColor(hex) {
        currentColor = hex;
        preview.style.background = hex;
        valueInput.value = hex;
      }

      function updatePalette() {
        palette.innerHTML = colors.slice(-10).map(c =>
          `<div style="width:100%;height:45px;background:${c};border-radius:8px;cursor:pointer;border:2px solid #e2e8f0;" onclick="window.setPickedColor('${c}')"></div>`
        ).join('');
      }

      window.setPickedColor = setColor;

      pickBtn.onclick = () => {
        pickBtn.textContent = '👆 Click anywhere...';
        const handler = (e) => {
          if (e.target.closest('.tw')) return;
          e.preventDefault();
          e.stopPropagation();

          const el = e.target;
          const style = window.getComputedStyle(el);
          const bg = style.backgroundColor;
          const rgb = bg.match(/\d+/g);
          const hex = '#' + rgb.map(x => ('0' + parseInt(x).toString(16)).slice(-2)).join('');

          setColor(hex);
          if (!colors.includes(hex)) {
            colors.push(hex);
            localStorage.setItem('aden-colors', JSON.stringify(colors));
            updatePalette();
          }

          pickBtn.textContent = '🎨 Pick Color from Page';
          document.removeEventListener('click', handler, true);
        };
        document.addEventListener('click', handler, true);
      };

      copyBtn.onclick = () => {
        navigator.clipboard.writeText(currentColor);
        copyBtn.textContent = '✓ Copied!';
        setTimeout(() => copyBtn.textContent = '📋 Copy to Clipboard', 1500);
      };

      setColor(currentColor);
      updatePalette();
    },

    darkmode: () => {
      const isDark = document.documentElement.classList.contains('aden-dark');
      if (isDark) {
        document.documentElement.classList.remove('aden-dark');
        const style = document.getElementById('aden-dark-style');
        if (style) style.remove();
      } else {
        const style = document.createElement('style');
        style.id = 'aden-dark-style';
        style.textContent = `
          html.aden-dark {filter: invert(1) hue-rotate(180deg);}
          html.aden-dark img, html.aden-dark video, html.aden-dark iframe {filter: invert(1) hue-rotate(180deg);}
        `;
        document.head.appendChild(style);
        document.documentElement.classList.add('aden-dark');
      }
      alert(isDark ? 'Dark mode disabled' : '🌙 Dark mode enabled! Run again to disable.');
    },

    videospeed: () => {
      const videos = Array.from(document.querySelectorAll('video'));
      if (videos.length === 0) return alert('No videos found on this page!');

      const win = createWindow('video', '⏩ Video Speed Controller', `
        <label class="tw-label">Playback Speed:</label>
        <input type="range" min="0.25" max="3" step="0.25" value="1" id="speed-slider" style="width:100%;">
        <div style="text-align:center;font-size:32px;font-weight:900;margin:15px 0;" id="speed-display">1.0x</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">
          ${[0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5].map(s =>
            `<button class="tw-btn tw-btn-secondary" data-speed="${s}" style="padding:12px;">${s}x</button>`
          ).join('')}
        </div>
        <div style="margin-top:15px;font-size:12px;color:#718096;text-align:center;">Found ${videos.length} video(s)</div>
      `, '400px');

      const slider = win.querySelector('#speed-slider');
      const display = win.querySelector('#speed-display');

      function setSpeed(speed) {
        videos.forEach(v => v.playbackRate = speed);
        display.textContent = speed.toFixed(2) + 'x';
        slider.value = speed;
      }

      slider.oninput = () => setSpeed(parseFloat(slider.value));
      win.querySelectorAll('[data-speed]').forEach(btn => {
        btn.onclick = () => setSpeed(parseFloat(btn.dataset.speed));
      });
    },

    snake: () => {
      const win = createWindow('snake', '🐍 Snake Game', `
        <div style="text-align:center;">
          <div style="font-size:24px;font-weight:700;margin-bottom:15px;">Score: <span id="snake-score">0</span></div>
          <canvas id="snake-canvas" width="300" height="300" style="border:3px solid #333;border-radius:8px;background:#f0f0f0;"></canvas>
          <button class="tw-btn tw-btn-primary" id="snake-restart" style="margin-top:15px;">🔄 Restart Game</button>
          <div style="font-size:12px;color:#718096;margin-top:10px;">Use arrow keys to play</div>
        </div>
      `, '360px');

      const canvas = win.querySelector('#snake-canvas');
      const ctx = canvas.getContext('2d');
      const scoreEl = win.querySelector('#snake-score');
      const restartBtn = win.querySelector('#snake-restart');

      const gridSize = 15;
      const tileSize = 20;
      let snake = [{x: 7, y: 7}];
      let dir = {x: 1, y: 0};
      let food = {x: 10, y: 10};
      let score = 0;
      let gameLoop;

      function draw() {
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, 300, 300);

        ctx.fillStyle = '#48bb78';
        snake.forEach(s => ctx.fillRect(s.x * tileSize, s.y * tileSize, tileSize - 2, tileSize - 2));

        ctx.fillStyle = '#f56565';
        ctx.fillRect(food.x * tileSize, food.y * tileSize, tileSize - 2, tileSize - 2);
      }

      function update() {
        const head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};

        if (head.x < 0 || head.x >= gridSize || head.y < 0 || head.y >= gridSize || snake.some(s => s.x === head.x && s.y === head.y)) {
          clearInterval(gameLoop);
          alert('Game Over! Score: ' + score);
          return;
        }

        snake.unshift(head);

        if (head.x === food.x && head.y === food.y) {
          score++;
          scoreEl.textContent = score;
          food = {x: Math.floor(Math.random() * gridSize), y: Math.floor(Math.random() * gridSize)};
        } else {
          snake.pop();
        }

        draw();
      }

      document.addEventListener('keydown', (e) => {
        if (!win.parentNode) return;
        if (e.key === 'ArrowUp' && dir.y === 0) dir = {x: 0, y: -1};
        if (e.key === 'ArrowDown' && dir.y === 0) dir = {x: 0, y: 1};
        if (e.key === 'ArrowLeft' && dir.x === 0) dir = {x: -1, y: 0};
        if (e.key === 'ArrowRight' && dir.x === 0) dir = {x: 1, y: 0};
      });

      function start() {
        snake = [{x: 7, y: 7}];
        dir = {x: 1, y: 0};
        score = 0;
        scoreEl.textContent = '0';
        food = {x: 10, y: 10};
        clearInterval(gameLoop);
        gameLoop = setInterval(update, 150);
        draw();
      }

      restartBtn.onclick = start;
      start();
    },
  };

  function launchTool(id) {
    if (TOOLS[id]) {
      TOOLS[id]();
    } else {
      alert('🚧 ' + id + ' coming soon!');
    }
  }

  showLauncher();

  // Global hotkey
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'K') {
      e.preventDefault();
      if (!document.querySelector('.tk-launcher')) {
        showLauncher();
      }
    }
  });

  console.log('%c🚀 Console Toolkit Hub Loaded!', 'font-size:20px;font-weight:bold;color:#667eea;');
  console.log('%c' + tools.length + ' tools available | Press Ctrl+Shift+K to open', 'font-size:12px;color:#764ba2;');
  console.log('%cCreated by Aden', 'font-size:11px;color:#999;');
})();
