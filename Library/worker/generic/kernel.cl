#define rotl32(a,n) rotate((a),(n))

#define rotl64(a,n) (rotate ((a), (n)))
#define rotr64(a,n) (rotate ((a), (64ul-n)))

#define mod(x,y) ((x)-((x)/(y)*(y)))

#define F2(x,y,z) ((x)^(y)^(z))
#define F1(x,y,z) (bitselect(z,y,x))
#define F0(x,y,z) (bitselect (x, y, ((x) ^ (z))))

#define SHA1M_A 0x67452301u
#define SHA1M_B 0xefcdab89u
#define SHA1M_C 0x98badcfeu
#define SHA1M_D 0x10325476u
#define SHA1M_E 0xc3d2e1f0u

#define SHA1C00 0x5a827999u
#define SHA1C01 0x6ed9eba1u
#define SHA1C02 0x8f1bbcdcu
#define SHA1C03 0xca62c1d6u

#define SHA1_STEP(f,a,b,c,d,e,x)\
{\
	e += K;\
	e += x;\
	e += f(b,c,d);\
	e += rotl32(a, 5u);\
	b = rotl32(b, 30u);\
}

unsigned long SWAP(const unsigned long val)
{
    // ab cd ef gh -> gh ef cd ab using the 32 bit trick
    unsigned long tmp = (rotr64(val & 0x0000FFFF0000FFFFUL, 16UL) | rotl64(val & 0xFFFF0000FFFF0000UL, 16UL));

    // Then see this as g- e- c- a- and -h -f -d -b to swap within the pairs,
    // gh ef cd ab -> hg fe dc ba
    return (rotr64(tmp & 0xFF00FF00FF00FF00UL, 8UL) | rotl64(tmp & 0x00FF00FF00FF00FFUL, 8UL));
}

unsigned long long count_digits(unsigned long input) {
    // counting digits
    if (input < 10000000000) {
        // [10,1]
        if (input < 100000) {
            // [5,1]
            if (input < 1000) {
                // [3,1]
                if (input < 100) {
                    // [2,1]
                    if (input < 10) {
                        return 1;
                    }
                    else {
                        return 2;
                    }
                }
                else {
                    return 3;
                }
            }
            else {
                if (input < 10000) {
                    return 4;
                }
                else {
                    return 5;
                }

            }
        }
        else {
            // [10,6]
            if (input < 100000000) {
                // [8,6]
                if (input < 10000000) {
                    // [7,6]
                    if (input < 1000000) {
                        return 6;
                    }
                    else {
                        return 7;
                    }
                }
                else {
                    return 8;
                }
            }
            else {
                if (input < 1000000000) {
                    return 9;
                }
                else {
                    return 10;
                }
            }
        }
    }
    else {
        // [20,11]
        if (input < 1000000000000000) {
            // [15,11]
            if (input < 10000000000000) {
                // [13,11]
                if (input < 1000000000000) {
                    if (input < 100000000000) {
                        return 11;
                    }
                    else {
                        return 12;
                    }
                }
                else {
                    return 13;
                }
            }
            else {
                //[15,14]
                if (input < 100000000000000) {
                    return 14;
                }
                else {
                    return 15;
                }
            }
        }
        else {
            // [20,16]
            if (input < 1000000000000000000) {
                // [18,16]
                if (input < 100000000000000000) {
                    // [17,16]
                    if (input < 10000000000000000) {
                        return 16;
                    }
                    else {
                        return 17;
                    }
                }
                else {
                    return 18;
                }
            }
            else {
                // [20,19]
                if (input < 10000000000000000000) {
                    return 19;
                }
                else {
                    return 20;
                }
            }
        }
    }
}


static void sha1_process2(const unsigned int *W, unsigned int *digest){
	unsigned int A = digest[0];
	unsigned int B = digest[1];
	unsigned int C = digest[2];
	unsigned int D = digest[3];
	unsigned int E = digest[4];
	
	unsigned int w0_t = W[0];
	unsigned int w1_t = W[1];
	unsigned int w2_t = W[2];
	unsigned int w3_t = W[3];
	unsigned int w4_t = W[4];
	unsigned int w5_t = W[5];
	unsigned int w6_t = W[6];
	unsigned int w7_t = W[7];
	unsigned int w8_t = W[8];
	unsigned int w9_t = W[9];
	unsigned int wa_t = W[10];
	unsigned int wb_t = W[11];
	unsigned int wc_t = W[12];
	unsigned int wd_t = W[13];
	unsigned int we_t = W[14];
	unsigned int wf_t = W[15];
	
	#undef K
	#define K SHA1C00
	
	SHA1_STEP (F1, A, B, C, D, E, w0_t);
	SHA1_STEP (F1, E, A, B, C, D, w1_t);
	SHA1_STEP (F1, D, E, A, B, C, w2_t);
	SHA1_STEP (F1, C, D, E, A, B, w3_t);
	SHA1_STEP (F1, B, C, D, E, A, w4_t);
	SHA1_STEP (F1, A, B, C, D, E, w5_t);
	SHA1_STEP (F1, E, A, B, C, D, w6_t);
	SHA1_STEP (F1, D, E, A, B, C, w7_t);
	SHA1_STEP (F1, C, D, E, A, B, w8_t);
	SHA1_STEP (F1, B, C, D, E, A, w9_t);
	SHA1_STEP (F1, A, B, C, D, E, wa_t);
	SHA1_STEP (F1, E, A, B, C, D, wb_t);
	SHA1_STEP (F1, D, E, A, B, C, wc_t);
	SHA1_STEP (F1, C, D, E, A, B, wd_t);
	SHA1_STEP (F1, B, C, D, E, A, we_t);
	SHA1_STEP (F1, A, B, C, D, E, wf_t);
	w0_t = rotl32 ((wd_t ^ w8_t ^ w2_t ^ w0_t), 1u); SHA1_STEP (F1, E, A, B, C, D, w0_t);
	w1_t = rotl32 ((we_t ^ w9_t ^ w3_t ^ w1_t), 1u); SHA1_STEP (F1, D, E, A, B, C, w1_t);
	w2_t = rotl32 ((wf_t ^ wa_t ^ w4_t ^ w2_t), 1u); SHA1_STEP (F1, C, D, E, A, B, w2_t);
	w3_t = rotl32 ((w0_t ^ wb_t ^ w5_t ^ w3_t), 1u); SHA1_STEP (F1, B, C, D, E, A, w3_t);
	
	#undef K
	#define K SHA1C01

	w4_t = rotl32 ((w1_t ^ wc_t ^ w6_t ^ w4_t), 1u); SHA1_STEP (F2, A, B, C, D, E, w4_t);
	w5_t = rotl32 ((w2_t ^ wd_t ^ w7_t ^ w5_t), 1u); SHA1_STEP (F2, E, A, B, C, D, w5_t);
	w6_t = rotl32 ((w3_t ^ we_t ^ w8_t ^ w6_t), 1u); SHA1_STEP (F2, D, E, A, B, C, w6_t);
	w7_t = rotl32 ((w4_t ^ wf_t ^ w9_t ^ w7_t), 1u); SHA1_STEP (F2, C, D, E, A, B, w7_t);
	w8_t = rotl32 ((w5_t ^ w0_t ^ wa_t ^ w8_t), 1u); SHA1_STEP (F2, B, C, D, E, A, w8_t);
	w9_t = rotl32 ((w6_t ^ w1_t ^ wb_t ^ w9_t), 1u); SHA1_STEP (F2, A, B, C, D, E, w9_t);
	wa_t = rotl32 ((w7_t ^ w2_t ^ wc_t ^ wa_t), 1u); SHA1_STEP (F2, E, A, B, C, D, wa_t);
	wb_t = rotl32 ((w8_t ^ w3_t ^ wd_t ^ wb_t), 1u); SHA1_STEP (F2, D, E, A, B, C, wb_t);
	wc_t = rotl32 ((w9_t ^ w4_t ^ we_t ^ wc_t), 1u); SHA1_STEP (F2, C, D, E, A, B, wc_t);
	wd_t = rotl32 ((wa_t ^ w5_t ^ wf_t ^ wd_t), 1u); SHA1_STEP (F2, B, C, D, E, A, wd_t);
	we_t = rotl32 ((wb_t ^ w6_t ^ w0_t ^ we_t), 1u); SHA1_STEP (F2, A, B, C, D, E, we_t);
	wf_t = rotl32 ((wc_t ^ w7_t ^ w1_t ^ wf_t), 1u); SHA1_STEP (F2, E, A, B, C, D, wf_t);
	w0_t = rotl32 ((wd_t ^ w8_t ^ w2_t ^ w0_t), 1u); SHA1_STEP (F2, D, E, A, B, C, w0_t);
	w1_t = rotl32 ((we_t ^ w9_t ^ w3_t ^ w1_t), 1u); SHA1_STEP (F2, C, D, E, A, B, w1_t);
	w2_t = rotl32 ((wf_t ^ wa_t ^ w4_t ^ w2_t), 1u); SHA1_STEP (F2, B, C, D, E, A, w2_t);
	w3_t = rotl32 ((w0_t ^ wb_t ^ w5_t ^ w3_t), 1u); SHA1_STEP (F2, A, B, C, D, E, w3_t);
	w4_t = rotl32 ((w1_t ^ wc_t ^ w6_t ^ w4_t), 1u); SHA1_STEP (F2, E, A, B, C, D, w4_t);
	w5_t = rotl32 ((w2_t ^ wd_t ^ w7_t ^ w5_t), 1u); SHA1_STEP (F2, D, E, A, B, C, w5_t);
	w6_t = rotl32 ((w3_t ^ we_t ^ w8_t ^ w6_t), 1u); SHA1_STEP (F2, C, D, E, A, B, w6_t);
	w7_t = rotl32 ((w4_t ^ wf_t ^ w9_t ^ w7_t), 1u); SHA1_STEP (F2, B, C, D, E, A, w7_t);

	#undef K
	#define K SHA1C02

	w8_t = rotl32 ((w5_t ^ w0_t ^ wa_t ^ w8_t), 1u); SHA1_STEP (F0, A, B, C, D, E, w8_t);
	w9_t = rotl32 ((w6_t ^ w1_t ^ wb_t ^ w9_t), 1u); SHA1_STEP (F0, E, A, B, C, D, w9_t);
	wa_t = rotl32 ((w7_t ^ w2_t ^ wc_t ^ wa_t), 1u); SHA1_STEP (F0, D, E, A, B, C, wa_t);
	wb_t = rotl32 ((w8_t ^ w3_t ^ wd_t ^ wb_t), 1u); SHA1_STEP (F0, C, D, E, A, B, wb_t);
	wc_t = rotl32 ((w9_t ^ w4_t ^ we_t ^ wc_t), 1u); SHA1_STEP (F0, B, C, D, E, A, wc_t);
	wd_t = rotl32 ((wa_t ^ w5_t ^ wf_t ^ wd_t), 1u); SHA1_STEP (F0, A, B, C, D, E, wd_t);
	we_t = rotl32 ((wb_t ^ w6_t ^ w0_t ^ we_t), 1u); SHA1_STEP (F0, E, A, B, C, D, we_t);
	wf_t = rotl32 ((wc_t ^ w7_t ^ w1_t ^ wf_t), 1u); SHA1_STEP (F0, D, E, A, B, C, wf_t);
	w0_t = rotl32 ((wd_t ^ w8_t ^ w2_t ^ w0_t), 1u); SHA1_STEP (F0, C, D, E, A, B, w0_t);
	w1_t = rotl32 ((we_t ^ w9_t ^ w3_t ^ w1_t), 1u); SHA1_STEP (F0, B, C, D, E, A, w1_t);
	w2_t = rotl32 ((wf_t ^ wa_t ^ w4_t ^ w2_t), 1u); SHA1_STEP (F0, A, B, C, D, E, w2_t);
	w3_t = rotl32 ((w0_t ^ wb_t ^ w5_t ^ w3_t), 1u); SHA1_STEP (F0, E, A, B, C, D, w3_t);
	w4_t = rotl32 ((w1_t ^ wc_t ^ w6_t ^ w4_t), 1u); SHA1_STEP (F0, D, E, A, B, C, w4_t);
	w5_t = rotl32 ((w2_t ^ wd_t ^ w7_t ^ w5_t), 1u); SHA1_STEP (F0, C, D, E, A, B, w5_t);
	w6_t = rotl32 ((w3_t ^ we_t ^ w8_t ^ w6_t), 1u); SHA1_STEP (F0, B, C, D, E, A, w6_t);
	w7_t = rotl32 ((w4_t ^ wf_t ^ w9_t ^ w7_t), 1u); SHA1_STEP (F0, A, B, C, D, E, w7_t);
	w8_t = rotl32 ((w5_t ^ w0_t ^ wa_t ^ w8_t), 1u); SHA1_STEP (F0, E, A, B, C, D, w8_t);
	w9_t = rotl32 ((w6_t ^ w1_t ^ wb_t ^ w9_t), 1u); SHA1_STEP (F0, D, E, A, B, C, w9_t);
	wa_t = rotl32 ((w7_t ^ w2_t ^ wc_t ^ wa_t), 1u); SHA1_STEP (F0, C, D, E, A, B, wa_t);
	wb_t = rotl32 ((w8_t ^ w3_t ^ wd_t ^ wb_t), 1u); SHA1_STEP (F0, B, C, D, E, A, wb_t);

	#undef K
	#define K SHA1C03

	wc_t = rotl32 ((w9_t ^ w4_t ^ we_t ^ wc_t), 1u); SHA1_STEP (F2, A, B, C, D, E, wc_t);
	wd_t = rotl32 ((wa_t ^ w5_t ^ wf_t ^ wd_t), 1u); SHA1_STEP (F2, E, A, B, C, D, wd_t);
	we_t = rotl32 ((wb_t ^ w6_t ^ w0_t ^ we_t), 1u); SHA1_STEP (F2, D, E, A, B, C, we_t);
	wf_t = rotl32 ((wc_t ^ w7_t ^ w1_t ^ wf_t), 1u); SHA1_STEP (F2, C, D, E, A, B, wf_t);
	w0_t = rotl32 ((wd_t ^ w8_t ^ w2_t ^ w0_t), 1u); SHA1_STEP (F2, B, C, D, E, A, w0_t);
	w1_t = rotl32 ((we_t ^ w9_t ^ w3_t ^ w1_t), 1u); SHA1_STEP (F2, A, B, C, D, E, w1_t);
	w2_t = rotl32 ((wf_t ^ wa_t ^ w4_t ^ w2_t), 1u); SHA1_STEP (F2, E, A, B, C, D, w2_t);
	w3_t = rotl32 ((w0_t ^ wb_t ^ w5_t ^ w3_t), 1u); SHA1_STEP (F2, D, E, A, B, C, w3_t);
	w4_t = rotl32 ((w1_t ^ wc_t ^ w6_t ^ w4_t), 1u); SHA1_STEP (F2, C, D, E, A, B, w4_t);
	w5_t = rotl32 ((w2_t ^ wd_t ^ w7_t ^ w5_t), 1u); SHA1_STEP (F2, B, C, D, E, A, w5_t);
	w6_t = rotl32 ((w3_t ^ we_t ^ w8_t ^ w6_t), 1u); SHA1_STEP (F2, A, B, C, D, E, w6_t);
	w7_t = rotl32 ((w4_t ^ wf_t ^ w9_t ^ w7_t), 1u); SHA1_STEP (F2, E, A, B, C, D, w7_t);
	w8_t = rotl32 ((w5_t ^ w0_t ^ wa_t ^ w8_t), 1u); SHA1_STEP (F2, D, E, A, B, C, w8_t);
	w9_t = rotl32 ((w6_t ^ w1_t ^ wb_t ^ w9_t), 1u); SHA1_STEP (F2, C, D, E, A, B, w9_t);
	wa_t = rotl32 ((w7_t ^ w2_t ^ wc_t ^ wa_t), 1u); SHA1_STEP (F2, B, C, D, E, A, wa_t);
	wb_t = rotl32 ((w8_t ^ w3_t ^ wd_t ^ wb_t), 1u); SHA1_STEP (F2, A, B, C, D, E, wb_t);
	wc_t = rotl32 ((w9_t ^ w4_t ^ we_t ^ wc_t), 1u); SHA1_STEP (F2, E, A, B, C, D, wc_t);
	wd_t = rotl32 ((wa_t ^ w5_t ^ wf_t ^ wd_t), 1u); SHA1_STEP (F2, D, E, A, B, C, wd_t);
	we_t = rotl32 ((wb_t ^ w6_t ^ w0_t ^ we_t), 1u); SHA1_STEP (F2, C, D, E, A, B, we_t);
	wf_t = rotl32 ((wc_t ^ w7_t ^ w1_t ^ wf_t), 1u); SHA1_STEP (F2, B, C, D, E, A, wf_t);

	// Macros don't have scope, so this K was being preserved
	#undef K

	digest[0] += A;
	digest[1] += B;
	digest[2] += C;
	digest[3] += D;
	digest[4] += E;
}

// main hashing function
void hash_function(__private unsigned int *string_to_hash,unsigned int string_length,__private unsigned int *hash,__private unsigned int *State){
	
	unsigned int plen = string_length/4;
	if(mod(string_length, 4)){
		plen++;
	}
	
	unsigned int W[0x10];
	
	int loops = plen;
	int curloop = 0;
	
	while(loops>0){
		W[0x0] = 0x0;
        W[0x1] = 0x0;
        W[0x2] = 0x0;
        W[0x3] = 0x0;
        W[0x4] = 0x0;
        W[0x5] = 0x0;
        W[0x6] = 0x0;
        W[0x7] = 0x0;
        W[0x8] = 0x0;
        W[0x9] = 0x0;
        W[0xA] = 0x0;
        W[0xB] = 0x0;
        W[0xC] = 0x0;
        W[0xD] = 0x0;
        W[0xE] = 0x0;
        W[0xF] = 0x0;
		
		for (int m=0;loops!=0 && m<16;m++)
        {
            W[m] ^= SWAP(string_to_hash[m+(curloop*16)]);
            loops--;
        }
        if (loops==0 && mod(string_length, 64)!=0)
        {
            unsigned int padding = 0x80<<(((string_length+4)-((string_length+4)/4*4))*8);
            int v = mod(string_length, 64);
            W[v/4] |= SWAP(padding);
            if ((string_length & 0x3B) != 0x3B)
            {
                // adding length
                W[0x0F] = string_length*8;
            }
        }
		
		sha1_process2(W, State);
		curloop++;
	}
	
	if (mod(plen,16) == 0){
        W[0x0] = 0x0;
        W[0x1] = 0x0;
        W[0x2] = 0x0;
        W[0x3] = 0x0;
        W[0x4] = 0x0;
        W[0x5] = 0x0;
        W[0x6] = 0x0;
        W[0x7] = 0x0;
        W[0x8] = 0x0;
        W[0x9] = 0x0;
        W[0xA] = 0x0;
        W[0xB] = 0x0;
        W[0xC] = 0x0;
        W[0xD] = 0x0;
        W[0xE] = 0x0;
        W[0xF] = 0x0;

        if ((string_length&0x3B) != 0x3B)
        {
            unsigned int padding=0x80 << (((string_length+4)-((string_length+4)/4*4))*8);
            W[0] |= SWAP(padding);
        }
        // adding length
        W[0x0F] = string_length*8;

        sha1_process2(W,State);
    }

    hash[0] = SWAP(State[0]);
    hash[1] = SWAP(State[1]);
    hash[2] = SWAP(State[2]);
    hash[3] = SWAP(State[3]);
    hash[4] = SWAP(State[4]);
}
	
#undef mod

#undef rotl32
#undef F0
#undef F1
#undef F2
	
__kernel void hash_main(__global unsigned char* last_hash, 
                        unsigned int last_hash_size,
                        unsigned long start,
                        __global unsigned long* result_buffer,
                        __global unsigned int* expected_hash,
                        unsigned long batch_size,
                        __global unsigned char* found,
                        __global unsigned int* cache_buffer)
{

    unsigned int cache_buffer_copy[5];
    // copy cache buffer
    cache_buffer_copy[0] = cache_buffer[0];
    cache_buffer_copy[1] = cache_buffer[1];
    cache_buffer_copy[2] = cache_buffer[2];
    cache_buffer_copy[3] = cache_buffer[3];
    cache_buffer_copy[4] = cache_buffer[4];


    unsigned int idx;
    idx = get_global_id(0);

    __private unsigned int outbuffer[5];
    __private unsigned char string_to_hash[60];
    unsigned int digits_count;
    digits_count = 0;
    unsigned long result;
    unsigned int full_size;
    unsigned char equal;
    
    
    // copy last_hash to string_to_hash
    for (unsigned char i = 0; i < last_hash_size; i++) {
        string_to_hash[i] = last_hash[i];
    }
    for (unsigned long batch_counter = 0; batch_counter < batch_size; batch_counter++) {
        result = start + idx*batch_size + batch_counter;
        if (found[0] == 1) {
            break;
        }
        // counting digits
        digits_count = count_digits(result);

        // converting integer to string representation
        result = start + idx * batch_size + batch_counter;
        // copy number string representation to string_to_hash
        for (char i = digits_count - 1; i > -1; i--) {
            string_to_hash[last_hash_size + i] = '0' + (result % 10);
            result /= 10;
        }
        full_size = last_hash_size + digits_count;

        // nulling rest of the array
        for (unsigned char i = full_size; i < 60; i++) {
            string_to_hash[i] = 0;
        }

        //if (start + idx * batch_size + batch_counter == 111802225) {
        //    // debug copy
        //    for (unsigned char i = 0; i < 52; i++) {
        //        debug_buffer[i] = string_to_hash[i];
        //    }
        //    debug_buffer[0] = digits_count;
        //}

        hash_function(string_to_hash, full_size, outbuffer, cache_buffer_copy);

        //if (start + idx * batch_size + batch_counter == 111802225) {
        //    // debug copy
        //    for (unsigned char i = 0; i < 5; i++) {
        //        debug_buffer[i] = outbuffer[i];
        //    }
        //    //debug_buffer[0] = full_size;
        //}

        
        equal = 1;
        for (unsigned char i = 0; i < 5; i++) {
            if (outbuffer[i] != expected_hash[i]) {
                equal = 0;

                break;
            }
        }


        if (equal == 1) {
            result_buffer[0] = 1;
            result_buffer[1] = start + idx * batch_size + batch_counter;
            found[0] = 1;
            break;
        }
    }
    //result_buffer[idx] = equal;
    
}
