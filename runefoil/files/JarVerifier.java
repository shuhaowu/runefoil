/*
 * Copyright (c) 2017, Adam <Adam@sigterm.info>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file is originally from
 * https://raw.githubusercontent.com/runelite/launcher/master/src/main/java/net/runelite/launcher/JarVerifier.java
 *
 * Modified to run via the command line.
 */
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.FileNotFoundException;
import java.nio.charset.StandardCharsets;
import java.security.cert.Certificate;
import java.security.cert.CertificateException;
import java.security.cert.CertificateFactory;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.Manifest;

public class JarVerifier
{

	private static String CERT =
		"-----BEGIN CERTIFICATE-----\n" +
		"MIIExTCCAq2gAwIBAgIESacoPTANBgkqhkiG9w0BAQsFADATMREwDwYDVQQDEwhy\n" +
		"dW5lbGl0ZTAeFw0xNzA0MTcxOTI1NDBaFw0yNzA0MTUxOTI1NDBaMBMxETAPBgNV\n" +
		"BAMTCHJ1bmVsaXRlMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEApglD\n" +
		"fuw2WnKLHN5grZ4V8LZFfiu7FcqXjsVaJTMPMi3wBbA6YbVKlDPiOdqfUDd5T2i+\n" +
		"yvH58DAnNC/MKm7zRt/TbOdv9kOK8yUSZDMlA6wqpGY5eb24NryWJ2sWlped3ZlK\n" +
		"0nzWHg2646Pejmj5uMPz49vOtVl5yh9ikD7mo9A6gQh/RKkUmhvww18fG9B2fS2B\n" +
		"MRQYiwrI5MOdJAg5GID505Eqfxz6SsDx4mJO9swSX24xduc8hU5CSK4C8TdSfA73\n" +
		"u2LM6u3Vt49kq4LE4i/LMQ55kMyIQyWKtf2kl9lIG1h4c9zjzMagiHHgsKKlSO8/\n" +
		"ck94DoIlvwQKS4SvBnw1ZQzJLXKx2WC7LpK4k4srr6YDtaPAnNNGSKP9xxLiUpJI\n" +
		"JKpYSdFWNa/i/stIjJ9pPBzVqkoY32YPGyxfp/ttfwwMQpFegpQUOruJ4lYfKNeM\n" +
		"l9gSm4VhO53v64y+bhiVYjEJEbeYP2Hg9JYvQPKhp571zIVvrIWLiLG9HmYad1Dl\n" +
		"23QOo5iZRdp6vUFAvzsT3o46lMv58YbVlz9mKOO7Mo1kZs3aSEHTex+MRkvndEr9\n" +
		"dBIGmG7CYHRA/N5mE9DtzMt2+zkBR3VLhB0urnWaX7teMa3oKFRj/1ShxznpRbwG\n" +
		"jzRHX5jYUk6rDZyhx9GoyxPCPCgf0wTlzRFLaZsCAwEAAaMhMB8wHQYDVR0OBBYE\n" +
		"FOoWEb2u2Y7i2DEZgpuGv7NQTq2zMA0GCSqGSIb3DQEBCwUAA4ICAQCIaBl+mdu5\n" +
		"JK4zeIxmlMRlSSfDnol2dtM4OmE+UsNrOz2/WThn8jCysRzGZxVKfTnQeR5RW1Pz\n" +
		"34UWPU1SivJpSwbChs9pIvjKEUu+FaE5u8OvysEfJ66isC0TK6aICuqAPCh2P+3a\n" +
		"EWX525LjNO3Roo1Di6hgY+y2lMTy0BSaZ1HfDDBt5Svr6G39TWgIFXmEuAknVKoz\n" +
		"QvVjOYbjVO6r7a4a0DRtgofSWdHQYGZSLgxSNUxbsRcQNA7D139UFv4nQxFeZPKY\n" +
		"lsHa28TCSMThW+cOvZGBj0WxrkHkQGSHDELq3V228KyPCcN2dXPba/IEJJ9Kw7L8\n" +
		"lLCtJx7L8ZpIEwSmJwdewPA0AkCDheBHb+0tAeYOJZEQB2QbB3MMsU/O4hyYrCdH\n" +
		"kGVJn8ONb+UNQ/l5U5tKCIsqqtxlEtysyWnW01qi7fbQ5psciiThXuSgd6Ftm+hh\n" +
		"hkbAHulJMz9wmEDMiJJXf/mv3e1KxMUAGwp0XAvSrq5IiLrQhOQXvqPsxTigefmk\n" +
		"5yhYepklO9T/7TypwmZ2WfugRmEl9Ni7hWwzQv8j5MA9XKlsmfSS2O0PcLyJbV2Q\n" +
		"0oOnPkZ+FoH+EINykP7UqnULO7PvM/KVs6tMy5r77HSo9OOTOexfXkb1UwqfY/hy\n" +
		"U6bay/LBPyrjloKRp6qBmEFj6PchK7FeJg==\n" +
		"-----END CERTIFICATE-----";

	public static void main(String[] args) {
		if (args.length == 0) {
			System.err.println("error: must provide a path");
			System.exit(1);
		}

		InputStream certInputStream = new ByteArrayInputStream(CERT.getBytes(StandardCharsets.UTF_8));
		JarFile jar = null;

		try {
			jar = new JarFile(args[0]);
		} catch (IOException ex) {
			System.err.println("error: failed to open jarfile at " + args[0] + ": " + ex);
			System.exit(1);
		}


		try {
			CertificateFactory certFactory = CertificateFactory.getInstance("X.509");
			Certificate certificate = certFactory.generateCertificate(certInputStream);
			verify(jar, certificate);
			System.out.println("signature verified");
		} catch (IOException | CertificateException | SecurityException ex) {
			System.err.println("cannot verify signature: " + ex);
			System.exit(1);
		}
	}

	/**
	 * Verify the jar is signed by the given certificate
	 * @param jarFile
	 * @param certificate
	 * @throws IOException
	 */
	public static void verify(JarFile jarFile, Certificate certificate) throws IOException
	{
		List<JarEntry> jarEntries = new ArrayList<>();

		// Ensure the jar file is signed.
		Manifest man = jarFile.getManifest();
		if (man == null)
		{
			throw new SecurityException("The provider is not signed");
		}

		// Ensure all the entries' signatures verify correctly
		byte[] buffer = new byte[8192];
		Enumeration entries = jarFile.entries();

		while (entries.hasMoreElements())
		{
			JarEntry je = (JarEntry) entries.nextElement();

			// Skip directories.
			if (je.isDirectory() || je.getName().startsWith("META-INF/"))
			{
				continue;
			}

			// Read in each jar entry. A security exception will
			// be thrown if a signature/digest check fails.
			try (InputStream is = jarFile.getInputStream(je))
			{
				// Read in each jar entry. A security exception will
				// be thrown if a signature/digest check fails.
				while (is.read(buffer, 0, buffer.length) != -1);
			}

			jarEntries.add(je);
		}

		// Get the list of signer certificates
		for (JarEntry je : jarEntries)
		{
			// Every file must be signed except files in META-INF.
			Certificate[] certs = je.getCertificates();
			if (certs == null || certs.length == 0)
			{
				throw new SecurityException("The jar contains an unsigned file: " + je);
			}

			Certificate cert = certs[0];

			if (!certificate.equals(cert))
			{
				throw new SecurityException("The jar is not signed by a trusted signer");
			}
		}
	}
}
