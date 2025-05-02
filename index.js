const express = require('express');
const multer = require('multer'); // To handle file uploads
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Configure storage
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
      cb(null, 'uploads/'); // folder to save
    },
    filename: (req, file, cb) => {
      const ext = path.extname(file.originalname); // get file extension
      const filename = Date.now() + ext; // give a unique name + extension
      cb(null, filename);
    }
  });


const app = express();
const upload = multer({ dest: 'uploads/', storage });


app.post('/scrape', upload.single('file'), (req, res) => {
    const filePath = req.file.path;
    console.log(filePath);

    // Call the Python script
    const python = spawn('C:/Users/USER/Desktop/project/venv/Scripts/python.exe', ['scrapper.py', filePath]);

    let resultData = '';

    python.stdout.on('data', (data) => {
        resultData += data.toString();
    });

    python.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    python.on('close', (code) => {
        fs.unlinkSync(filePath); // Delete uploaded file after processing

        if (code === 0) {
            // res.json({ result: JSON.parse(resultData) }); // Assuming your python script prints JSON
            res.sendStatus(200);
        } else {
            res.status(500).send('Python script failed');
        }
    });
});

app.listen(8080, () => console.log('Server running on http://localhost:8080'));
