package com.example.demo.service; // Note the package change

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

    public ResponseEntity<String> processReconcile(MultipartFile ethFile, MultipartFile zzbFile) {
        return forwardToFastApi("/reconcile", ethFile, zzbFile, String.class);
    }

    public ResponseEntity<Resource> downloadReconcile(MultipartFile ethFile, MultipartFile zzbFile) {
        return forwardToFastApi("/reconcile/download", ethFile, zzbFile, Resource.class);
    }

    private <T> ResponseEntity<T> forwardToFastApi(String endpoint, MultipartFile eth, MultipartFile zzb, Class<T> responseType) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("eth_file", eth.getResource());
        body.add("zzb_file", zzb.getResource());

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        return restTemplate.postForEntity(fastApiBaseUrl + endpoint, requestEntity, responseType);
    }
}