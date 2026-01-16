package com.example.demo.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@Service
public class ReconciliationService {

    @Value("${fastapi.url}")
    private String fastApiBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    // FIXED: Added reconType and removed the trailing comma after zzbFile
    public ResponseEntity<String> processReconcile(MultipartFile ethFile, MultipartFile zzbFile, String reconType) {
        return forwardToFastApi("/reconcile", ethFile, zzbFile, reconType, String.class);
    }

    // FIXED: Added reconType to parameters
    public ResponseEntity<Resource> downloadReconcile(MultipartFile ethFile, MultipartFile zzbFile, String reconType) {
        return forwardToFastApi("/reconcile/download", ethFile, zzbFile, reconType, Resource.class);
    }

    // This method expects 5 arguments, we must pass all 5 from the methods above
    private <T> ResponseEntity<T> forwardToFastApi(String endpoint, MultipartFile eth, MultipartFile zzb, String reconType, Class<T> responseType) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("eth_file", eth.getResource());
        body.add("zzb_file", zzb.getResource());
        body.add("recon_type", reconType); // This maps to the Form("atm") in FastAPI

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        return restTemplate.postForEntity(fastApiBaseUrl + endpoint, requestEntity, responseType);
    }
}