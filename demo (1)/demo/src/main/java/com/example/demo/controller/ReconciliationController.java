package com.example.demo.controller; // Note the package change

import com.example.demo.service.ReconciliationService; // Import the service
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/reconcile")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") 
public class ReconciliationController {

    private final ReconciliationService reconciliationService;

    @PostMapping
    public ResponseEntity<String> reconcile(
            @RequestParam("eth_file") MultipartFile ethFile,
            @RequestParam("zzb_file") MultipartFile zzbFile) {
        return reconciliationService.processReconcile(ethFile, zzbFile);
    }

    @PostMapping("/download")
    public ResponseEntity<Resource> download(
            @RequestParam("eth_file") MultipartFile ethFile,
            @RequestParam("zzb_file") MultipartFile zzbFile) {
        return reconciliationService.downloadReconcile(ethFile, zzbFile);
    }
}